"""Relational audit model for trusted sources, documents, versions, and chunks."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import AuthBase


class KnowledgeSource(AuthBase):
    """A reviewed source group and its configurable check state."""

    __tablename__ = "sahayak_knowledge_sources"

    key: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(96), nullable=False)
    authority_level: Mapped[int] = mapped_column(Integer, nullable=False)
    geographic_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    check_interval_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_domains: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    entry_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    expected_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    discovery_path_prefixes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    max_documents_per_check: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="APPROVED")
    last_successful_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_detected_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_successful_ingestion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeDocument(AuthBase):
    """Stable identity of an official document across its immutable versions."""

    __tablename__ = "sahayak_knowledge_documents"
    __table_args__ = (
        UniqueConstraint("source_key", "canonical_url", name="sahayak_knowledge_document_source_url_key"),
        Index("sahayak_knowledge_documents_source_idx", "source_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("sahayak_knowledge_sources.key", ondelete="RESTRICT"), nullable=False
    )
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_metadata: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeDocumentVersion(AuthBase):
    """One retained, auditable version of a source document."""

    __tablename__ = "sahayak_knowledge_document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="sahayak_knowledge_document_version_number_key"),
        Index("sahayak_knowledge_document_versions_current_idx", "status", "effective_at"),
        Index("sahayak_knowledge_document_versions_hash_idx", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("sahayak_knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    publication_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    storage_reference: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(String(64))
    is_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ocr_confidence: Mapped[float | None] = mapped_column()
    source_metadata: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    # Categories come from the reviewed crawl target, never an LLM inference.
    # They make coverage measurable independently of fetch/check success.
    coverage_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class KnowledgeChunk(AuthBase):
    """A semantic chunk whose vector point lives in Qdrant, not the browser."""

    __tablename__ = "sahayak_knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_version_id", "ordinal", name="sahayak_knowledge_chunk_ordinal_key"),
        Index("sahayak_knowledge_chunks_hash_idx", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_version_id: Mapped[str] = mapped_column(
        ForeignKey("sahayak_knowledge_document_versions.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    vector_point_id: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    page_number: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(24), index=True)
    state: Mapped[str | None] = mapped_column(String(100), index=True)
    district: Mapped[str | None] = mapped_column(String(120), index=True)
    scheme_key: Mapped[str | None] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class KnowledgeSourceCheck(AuthBase):
    """Append-only operational history; failure messages remain non-sensitive."""

    __tablename__ = "sahayak_knowledge_source_checks"
    __table_args__ = (
        Index("sahayak_knowledge_source_checks_source_started_idx", "source_key", "started_at"),
        # A source group can have exactly one active check, even if a scheduler
        # retries while a prior worker is still running. This is supported by
        # both local SQLite and production PostgreSQL.
        Index(
            "sahayak_knowledge_source_checks_one_open_per_source",
            "source_key",
            unique=True,
            sqlite_where=text("completed_at IS NULL"),
            postgresql_where=text("completed_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("sahayak_knowledge_sources.key", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    checked_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changed_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(96))
    details: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)


class KnowledgeFailedResource(AuthBase):
    """Retry-safe audit state for one official resource that could not be processed."""

    __tablename__ = "sahayak_knowledge_failed_resources"
    __table_args__ = (
        UniqueConstraint("source_key", "canonical_url", name="sahayak_knowledge_failed_resource_source_url_key"),
        Index("sahayak_knowledge_failed_resources_retry_idx", "source_key", "next_retry_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("sahayak_knowledge_sources.key", ondelete="CASCADE"), nullable=False
    )
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    failure_code: Mapped[str] = mapped_column(String(96), nullable=False)
    first_failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
