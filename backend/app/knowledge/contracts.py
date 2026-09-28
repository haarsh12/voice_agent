"""Typed contracts shared by knowledge ingestion, retrieval, and chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Lifecycle state of one immutable source-document version."""

    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNKNOWN = "UNKNOWN"
    FETCH_FAILED = "FETCH_FAILED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class SourceValidationStatus(str, Enum):
    """Whether a source remains usable for verified answers."""

    APPROVED = "APPROVED"
    DISABLED = "DISABLED"
    CHECK_FAILED = "CHECK_FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class EvidenceStatus(str, Enum):
    """The evidence classification sent to the visual client."""

    VERIFIED_SOURCE = "VERIFIED_SOURCE"
    MULTIPLE_VERIFIED_SOURCES = "MULTIPLE_VERIFIED_SOURCES"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    GENERAL_MODEL_KNOWLEDGE = "GENERAL_MODEL_KNOWLEDGE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SourceCheckResult(str, Enum):
    """Auditable outcome of an offline source check."""

    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    FAILED = "FAILED"


@dataclass(frozen=True)
class UserKnowledgeContext:
    """Optional profile fields used only to rank/filter trusted evidence."""

    state: str | None = None
    district: str | None = None
    village_or_town: str | None = None
    user_type: str | None = None
    cooperative_role: str | None = None


@dataclass(frozen=True)
class Citation:
    """A citation generated only from retrieved, approved source metadata."""

    source_name: str
    title: str
    url: str
    document_version: str | None = None
    published_at: datetime | None = None
    effective_at: datetime | None = None
    freshness_status: DocumentStatus = DocumentStatus.UNKNOWN


@dataclass(frozen=True)
class RetrievedEvidence:
    """One trusted semantic chunk and its provenance for model grounding."""

    chunk_id: str
    text: str
    score: float
    citation: Citation
    source_priority: int
    state: str | None = None
    district: str | None = None
    language: str | None = None


@dataclass(frozen=True)
class RetrievalResult:
    """Result of the source-grounded online retrieval path."""

    evidence: tuple[RetrievedEvidence, ...] = ()
    unavailable_reason: str | None = None

    @property
    def citations(self) -> tuple[Citation, ...]:
        """Return unique citations in retrieval order."""

        unique: dict[tuple[str, str, str | None], Citation] = {}
        for item in self.evidence:
            key = (item.citation.source_name, item.citation.url, item.citation.document_version)
            unique.setdefault(key, item.citation)
        return tuple(unique.values())


@dataclass(frozen=True)
class KnowledgeDecision:
    """What the chat route may safely do after source retrieval."""

    evidence_status: EvidenceStatus
    retrieval: RetrievalResult
    requires_abstention: bool
    abstention_message: str | None = None


@dataclass(frozen=True)
class FetchedDocument:
    """Validated result of downloading one approved source document."""

    url: str
    canonical_url: str
    content: bytes
    content_type: str
    content_hash: str
    etag: str | None = None
    last_modified: str | None = None
    fetched_at: datetime | None = None


@dataclass(frozen=True)
class ExtractedSourceDocument:
    """Text and extraction metadata while retaining the original source URL."""

    text: str
    title: str
    page_count: int | None
    extraction_method: str
    is_ocr: bool = False
    ocr_confidence: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)
