"""Deterministic semantic chunking for official source text."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_WHITESPACE = re.compile(r"[ \t]+")
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n+")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?।])\s+")
_NUMBERED_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*[.)]|[A-Z][.)])\s+.+")


@dataclass(frozen=True)
class SemanticChunk:
    """A heading-aware piece of source content with a stable content hash."""

    content: str
    content_hash: str
    heading: str | None = None
    page_number: int | None = None


def chunk_semantically(text: str, *, max_characters: int = 1_200, min_characters: int = 180) -> list[SemanticChunk]:
    """Group paragraphs by section, splitting only oversized paragraphs by sentences.

    Fixed character windows can detach a deadline, exception, or eligibility
    clause from its heading. This keeps those boundaries intact whenever the
    source format makes them available and is deterministic for idempotency.
    """

    if max_characters < 400:
        raise ValueError("max_characters must preserve meaningful source context")

    raw_pages = text.split("\f")
    page_numbered = len(raw_pages) > 1
    chunks: list[SemanticChunk] = []
    for index, raw_page in enumerate(raw_pages, start=1):
        normalized = _normalize_text(raw_page)
        if normalized:
            chunks.extend(
                _chunk_page(
                    normalized,
                    page_number=index if page_numbered else None,
                    max_characters=max_characters,
                    min_characters=min_characters,
                )
            )
    return chunks


def _chunk_page(
    normalized: str,
    *,
    page_number: int | None,
    max_characters: int,
    min_characters: int,
) -> list[SemanticChunk]:
    """Chunk one source page so citations retain a precise page reference."""

    chunks: list[SemanticChunk] = []
    heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        content = "\n\n".join(buffer).strip()
        if content:
            chunks.append(_chunk(content, heading, page_number))
        buffer = []

    for paragraph in _PARAGRAPH_BREAK.split(normalized):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if _is_heading(paragraph):
            flush()
            heading = paragraph[:500]
            continue
        candidates = _split_oversized_paragraph(paragraph, max_characters)
        for candidate in candidates:
            projected_size = len("\n\n".join([*buffer, candidate]))
            if buffer and projected_size > max_characters:
                flush()
            buffer.append(candidate)
            # A substantive paragraph should be queryable promptly rather
            # than waiting for unrelated following sections.
            if len("\n\n".join(buffer)) >= max_characters - min_characters:
                flush()
    flush()

    # A trailing short fragment is usually a continuation of the prior clause.
    if (
        len(chunks) >= 2
        and len(chunks[-1].content) < min_characters
        and chunks[-1].heading == chunks[-2].heading
    ):
        previous, tail = chunks[-2], chunks[-1]
        combined = f"{previous.content}\n\n{tail.content}"
        if len(combined) <= max_characters + min_characters:
            chunks[-2:] = [_chunk(combined, previous.heading or tail.heading, page_number)]
    return chunks


def _normalize_text(value: str) -> str:
    lines = [_WHITESPACE.sub(" ", line).strip() for line in value.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip()


def _is_heading(paragraph: str) -> bool:
    line_count = paragraph.count("\n") + 1
    if line_count != 1 or len(paragraph) > 180:
        return False
    if paragraph.startswith("#") or _NUMBERED_HEADING.fullmatch(paragraph):
        return True
    letters = [character for character in paragraph if character.isalpha()]
    return bool(letters) and len(letters) >= 4 and sum(character.isupper() for character in letters) / len(letters) > 0.8


def _split_oversized_paragraph(paragraph: str, max_characters: int) -> list[str]:
    if len(paragraph) <= max_characters:
        return [paragraph]
    sentences = _SENTENCE_BREAK.split(paragraph)
    pieces: list[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_characters:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.extend(sentence[index : index + max_characters] for index in range(0, len(sentence), max_characters))
            continue
        candidate = f"{buffer} {sentence}".strip()
        if buffer and len(candidate) > max_characters:
            pieces.append(buffer)
            buffer = sentence
        else:
            buffer = candidate
    if buffer:
        pieces.append(buffer)
    return pieces


def _chunk(content: str, heading: str | None, page_number: int | None) -> SemanticChunk:
    return SemanticChunk(
        content=content,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        heading=heading,
        page_number=page_number,
    )
