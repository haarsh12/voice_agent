"""Approved OCR adapters for scanned official documents.

OCR is opt-in and runs only in the offline ingestion worker. The implementation
uses the service account already configured for Google Cloud/Vertex; image
bytes never pass through the browser or a model prompt.
"""

from __future__ import annotations

from io import BytesIO
from typing import Protocol

from pypdf import PdfReader

from app.config.settings import MissingConfigurationError, Settings
from app.knowledge.contracts import ExtractedSourceDocument, FetchedDocument
from app.services.gemini import load_vertex_authentication


class OcrError(RuntimeError):
    """Raised without exposing document content or cloud-provider details."""


class OcrProvider(Protocol):
    """A reviewed server-side OCR capability."""

    def extract_pdf(self, document: FetchedDocument) -> ExtractedSourceDocument:
        """Return page-preserving text for a scanned, approved PDF."""


def create_ocr_provider(settings: Settings) -> OcrProvider | None:
    """Build the explicitly configured provider; disabled remains fail-closed."""

    if settings.knowledge_ocr_provider == "disabled":
        return None
    if settings.knowledge_ocr_provider == "google_cloud_vision":
        return GoogleCloudVisionOcrProvider(settings)
    raise MissingConfigurationError("KNOWLEDGE_OCR_PROVIDER is not an approved OCR provider.")


class GoogleCloudVisionOcrProvider:
    """Google Cloud Vision OCR with bounded, local PDF rendering."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract_pdf(self, document: FetchedDocument) -> ExtractedSourceDocument:
        try:
            import pymupdf  # PyMuPDF is intentionally used only by this adapter.
            from google.cloud import vision

            reader = PdfReader(BytesIO(document.content), strict=False)
            page_count = len(reader.pages)
            if not page_count:
                raise OcrError("ocr_pdf_has_no_pages")
            if page_count > self.settings.knowledge_ocr_max_pages:
                raise OcrError("ocr_pdf_exceeds_page_limit")

            authentication = load_vertex_authentication(self.settings)
            client = vision.ImageAnnotatorClient(credentials=authentication.credentials)
            rendered = pymupdf.open(stream=document.content, filetype="pdf")
            try:
                page_text: list[str] = []
                confidences: list[float] = []
                scale = self.settings.knowledge_ocr_render_dpi / 72
                for page in rendered:
                    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
                    response = client.document_text_detection(
                        image=vision.Image(content=pixmap.tobytes("png"))
                    )
                    if response.error.message:
                        raise OcrError("ocr_provider_rejected_document")
                    text = (response.full_text_annotation.text or "").strip()
                    if not text:
                        raise OcrError("ocr_page_has_no_text")
                    page_text.append(text)
                    confidences.extend(_word_confidences(response.full_text_annotation))
            finally:
                rendered.close()
        except (ImportError, MissingConfigurationError, OcrError):
            raise
        except Exception as error:
            raise OcrError("ocr_processing_failed") from error

        return ExtractedSourceDocument(
            text="\f".join(page_text),
            title=_title_from_url(document.url),
            page_count=page_count,
            extraction_method="google_cloud_vision_ocr",
            is_ocr=True,
            ocr_confidence=(sum(confidences) / len(confidences)) if confidences else None,
        )


def _word_confidences(annotation: object) -> list[float]:
    values: list[float] = []
    for page in getattr(annotation, "pages", ()):
        for block in getattr(page, "blocks", ()):
            for paragraph in getattr(block, "paragraphs", ()):
                for word in getattr(paragraph, "words", ()):
                    confidence = getattr(word, "confidence", None)
                    if isinstance(confidence, (float, int)) and 0 <= confidence <= 1:
                        values.append(float(confidence))
    return values


def _title_from_url(url: str) -> str:
    filename = url.rstrip("/").rsplit("/", 1)[-1]
    return filename or "Official source document"
