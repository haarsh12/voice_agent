"""Safe, request-scoped extraction of text from supported document uploads."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import warnings
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from starlette.datastructures import UploadFile

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 60_000
MAX_PDF_PAGES = 75
MAX_DOCX_MEMBERS = 1_000
MAX_DOCX_UNCOMPRESSED_BYTES = 30 * 1024 * 1024
MAX_DOCX_DOCUMENT_XML_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_DIMENSION = 8_192

_TEXT_SUFFIXES = frozenset({".txt", ".md"})
_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})
_SUPPORTED_SUFFIXES = _TEXT_SUFFIXES | _IMAGE_SUFFIXES | frozenset({".pdf", ".docx"})
_ALLOWED_CONTENT_TYPES: dict[str, frozenset[str]] = {
    ".txt": frozenset({"text/plain"}),
    ".md": frozenset({"text/markdown", "text/plain"}),
    ".pdf": frozenset({"application/pdf"}),
    ".docx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
    ".jpg": frozenset({"image/jpeg", "image/jpg"}),
    ".jpeg": frozenset({"image/jpeg", "image/jpg"}),
    ".png": frozenset({"image/png"}),
}
_WORDPROCESSING_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocumentExtractionError(ValueError):
    """Raised for user-facing, safe document validation failures."""


@dataclass(frozen=True)
class ExtractedDocument:
    """Plain text made available only to the current chat request."""

    filename: str
    text: str
    truncated: bool


@dataclass(frozen=True)
class ExtractedImage:
    """A validated image retained only in request memory for Gemini analysis."""

    filename: str
    data: bytes
    mime_type: str
    width: int
    height: int


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "document").name.strip()
    if not name or len(name) > 180:
        raise DocumentExtractionError("The document name is invalid.")
    return name


def _limit_text(text: str) -> tuple[str, bool]:
    normalized = text.replace("\x00", "").strip()
    if not normalized:
        raise DocumentExtractionError(
            "No readable text was found. For scanned documents, upload a text-based PDF or paste the text."
        )
    if len(normalized) <= MAX_EXTRACTED_CHARACTERS:
        return normalized, False
    return normalized[:MAX_EXTRACTED_CHARACTERS].rstrip(), True


def _extract_text_document(raw: bytes) -> tuple[str, bool]:
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DocumentExtractionError("Text documents must use UTF-8 encoding.") from error
    return _limit_text(decoded)


def _extract_pdf(raw: bytes) -> tuple[str, bool]:
    try:
        reader = PdfReader(BytesIO(raw), strict=False)
    except (PdfReadError, ValueError, TypeError) as error:
        raise DocumentExtractionError("The PDF could not be read.") from error

    if reader.is_encrypted:
        raise DocumentExtractionError("Password-protected PDFs are not supported.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise DocumentExtractionError(f"PDFs are limited to {MAX_PDF_PAGES} pages.")

    parts: list[str] = []
    length = 0
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception as error:
            raise DocumentExtractionError("Text could not be extracted from this PDF.") from error
        if not page_text:
            continue
        remaining = MAX_EXTRACTED_CHARACTERS - length
        if remaining <= 0:
            return "\n\n".join(parts).strip(), True
        if len(page_text) > remaining:
            parts.append(page_text[:remaining])
            return "\n\n".join(parts).strip(), True
        parts.append(page_text)
        length += len(page_text)

    return _limit_text("\n\n".join(parts))


def _extract_docx(raw: bytes) -> tuple[str, bool]:
    try:
        with ZipFile(BytesIO(raw)) as archive:
            members = archive.infolist()
            if len(members) > MAX_DOCX_MEMBERS:
                raise DocumentExtractionError("The DOCX contains too many embedded files.")
            if sum(member.file_size for member in members) > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise DocumentExtractionError("The DOCX expands beyond the allowed size.")

            try:
                document_info = archive.getinfo("word/document.xml")
            except KeyError as error:
                raise DocumentExtractionError("The DOCX document content is missing.") from error
            if document_info.file_size > MAX_DOCX_DOCUMENT_XML_BYTES:
                raise DocumentExtractionError("The DOCX text content is too large.")
            document_xml = archive.read(document_info)
    except BadZipFile as error:
        raise DocumentExtractionError("The DOCX file is invalid.") from error

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as error:
        raise DocumentExtractionError("The DOCX text content is invalid.") from error

    paragraphs: list[str] = []
    for paragraph in root.iter(f"{_WORDPROCESSING_NAMESPACE}p"):
        value = "".join(node.text or "" for node in paragraph.iter(f"{_WORDPROCESSING_NAMESPACE}t"))
        if value:
            paragraphs.append(value)
    return _limit_text("\n".join(paragraphs))


def _extract_image(raw: bytes, suffix: str) -> tuple[str, int, int]:
    """Verify image bytes and reject deceptive or decompression-bomb images."""

    expected_format = "PNG" if suffix == ".png" else "JPEG"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format != expected_format:
                    raise DocumentExtractionError("The image contents do not match its file extension.")
                width, height = image.size
                if (
                    width <= 0
                    or height <= 0
                    or width > MAX_IMAGE_DIMENSION
                    or height > MAX_IMAGE_DIMENSION
                    or width * height > MAX_IMAGE_PIXELS
                ):
                    raise DocumentExtractionError(
                        "Images must be at most 8,192 pixels per side and 20 megapixels."
                    )
                image.load()
    except DocumentExtractionError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise DocumentExtractionError("The image dimensions are too large.") from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise DocumentExtractionError("The image could not be read.") from error

    return ("image/png" if expected_format == "PNG" else "image/jpeg"), width, height


async def extract_uploaded_document(upload: UploadFile) -> ExtractedDocument | ExtractedImage:
    """Validate an upload without writing it to application storage."""

    filename = _safe_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise DocumentExtractionError("Only TXT, Markdown, PDF, DOCX, JPEG, and PNG files are supported.")

    content_type = (upload.content_type or "").lower().strip()
    if content_type and content_type != "application/octet-stream":
        if content_type not in _ALLOWED_CONTENT_TYPES[suffix]:
            raise DocumentExtractionError("The document type does not match its file extension.")

    try:
        raw = await upload.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await upload.close()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise DocumentExtractionError("Documents must be 5 MB or smaller.")
    if not raw:
        raise DocumentExtractionError("The document is empty.")

    if suffix in _TEXT_SUFFIXES:
        text, truncated = _extract_text_document(raw)
    elif suffix == ".pdf":
        text, truncated = _extract_pdf(raw)
    elif suffix == ".docx":
        text, truncated = _extract_docx(raw)
    else:
        mime_type, width, height = _extract_image(raw, suffix)
        return ExtractedImage(
            filename=filename,
            data=raw,
            mime_type=mime_type,
            width=width,
            height=height,
        )
    return ExtractedDocument(filename=filename, text=text, truncated=truncated)
