"""Safe extraction of text from downloaded, approved source documents."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from io import BytesIO
from zipfile import ZipFile

from pypdf import PdfReader

from app.knowledge.contracts import ExtractedSourceDocument, FetchedDocument
from app.knowledge.ocr import OcrProvider


class SourceExtractionError(RuntimeError):
    """Raised when approved source bytes cannot be safely extracted."""


class _VisibleTextParser(HTMLParser):
    """Minimal dependency-free HTML extractor that ignores executable content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._hidden_depth = 0
        self._title: list[str] = []
        self._text: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self._hidden_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "div", "section", "article", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"} and self._hidden_depth:
            self._hidden_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._hidden_depth:
            return
        if self._in_title:
            self._title.append(data)
        self._text.append(data)

    @property
    def title(self) -> str:
        return _clean(" ".join(self._title))

    @property
    def text(self) -> str:
        return _clean("".join(self._text))


def extract_source_document(
    document: FetchedDocument,
    *,
    ocr_provider: OcrProvider | None = None,
    max_pdf_pages: int = 300,
) -> ExtractedSourceDocument:
    """Extract a bounded text representation without executing remote content."""

    content_type = document.content_type.split(";", 1)[0].strip().lower()
    try:
        if content_type in {"text/html", "application/xhtml+xml"}:
            return _extract_html(document)
        if content_type == "application/pdf" or document.url.lower().endswith(".pdf"):
            return _extract_pdf(
                document,
                ocr_provider=ocr_provider,
                max_pdf_pages=max_pdf_pages,
            )
        if content_type in {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        } or document.url.lower().endswith(".docx"):
            return _extract_docx(document)
        if content_type.startswith("text/") or content_type in {"application/json", "application/xml", "text/xml"}:
            text = document.content.decode("utf-8", errors="replace")
            return ExtractedSourceDocument(text=_clean(text), title=_title_from_url(document.url), page_count=None, extraction_method="text")
    except Exception as error:
        raise SourceExtractionError("approved source content could not be extracted") from error
    raise SourceExtractionError("approved source content type is not supported")


def _extract_html(document: FetchedDocument) -> ExtractedSourceDocument:
    parser = _VisibleTextParser()
    parser.feed(document.content.decode("utf-8", errors="replace"))
    text = parser.text
    if not text:
        raise SourceExtractionError("approved HTML source did not contain readable text")
    return ExtractedSourceDocument(text=text, title=parser.title or _title_from_url(document.url), page_count=None, extraction_method="html")


def _extract_pdf(
    document: FetchedDocument,
    *,
    ocr_provider: OcrProvider | None,
    max_pdf_pages: int,
) -> ExtractedSourceDocument:
    reader = PdfReader(BytesIO(document.content), strict=False)
    if len(reader.pages) > max_pdf_pages:
        raise SourceExtractionError("PDF exceeds the configured page limit")
    pages = [_clean(page.extract_text() or "") for page in reader.pages]
    text = "\f".join(pages)
    if not any(pages):
        if ocr_provider is None:
            raise SourceExtractionError("PDF needs an approved OCR extraction adapter")
        return ocr_provider.extract_pdf(document)
    title = _clean(str(reader.metadata.title)) if reader.metadata and reader.metadata.title else _title_from_url(document.url)
    return ExtractedSourceDocument(text=text, title=title, page_count=len(reader.pages), extraction_method="pdf_text")


def _extract_docx(document: FetchedDocument) -> ExtractedSourceDocument:
    with ZipFile(BytesIO(document.content)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    text = _clean(re.sub(r"<[^>]+>", " ", xml))
    if not text:
        raise SourceExtractionError("DOCX did not contain readable text")
    return ExtractedSourceDocument(text=text, title=_title_from_url(document.url), page_count=None, extraction_method="docx")


def _clean(value: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", value)).strip()


def _title_from_url(url: str) -> str:
    filename = url.rstrip("/").rsplit("/", 1)[-1]
    return filename or "Official source document"
