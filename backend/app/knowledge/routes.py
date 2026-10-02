"""Public, deliberately sanitized knowledge-base transparency endpoint."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import get_auth_session
from app.auth.rate_limit import SlidingWindowRateLimiter
from app.config.settings import Settings, get_settings
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.vectors import QdrantVectorStore, VectorStoreError

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
_logger = logging.getLogger("sahayak.knowledge.public_status")
_status_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)
_vector_summary_lock = asyncio.Lock()
_vector_summary_cache: tuple[datetime, str, int | None] | None = None
_VECTOR_STATUS_CACHE_SECONDS = 30


class KnowledgeBaseStorageSummary(BaseModel):
    """Counts and readiness only; connection details and credentials stay private."""

    vector_index: Literal["connected", "not_configured", "unavailable"]
    vector_point_count: int | None = Field(default=None, ge=0)
    source_count: int = Field(ge=0)
    document_count: int = Field(ge=0)
    current_document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)


class KnowledgeBaseCheckSummary(BaseModel):
    started_at: datetime
    completed_at: datetime | None = None
    result: Literal["UNCHANGED", "CHANGED", "PARTIAL_FAILURE", "FAILED"]
    checked_documents: int = Field(ge=0)
    changed_documents: int = Field(ge=0)


class KnowledgeBaseSourceSummary(BaseModel):
    key: str
    name: str
    category: str
    geographic_scope: str
    approved_domains: list[str]
    entry_urls: list[str]
    expected_categories: list[str]
    covered_categories: list[str]
    missing_categories: list[str]
    coverage_state: Literal["COMPLETE", "PARTIAL", "INCOMPLETE", "UNKNOWN"]
    ingestion_state: Literal["INGESTED", "NOT_INGESTED"]
    failed_resource_count: int = Field(ge=0)
    validation_status: Literal["APPROVED", "DISABLED", "CHECK_FAILED", "REVIEW_REQUIRED"]
    check_interval_hours: int = Field(ge=1)
    last_successful_check_at: datetime | None = None
    last_detected_change_at: datetime | None = None
    last_successful_ingestion_at: datetime | None = None
    current_document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    latest_check: KnowledgeBaseCheckSummary | None = None


class KnowledgeBaseDocumentSummary(BaseModel):
    source_key: str
    source_name: str
    title: str
    url: str
    version_number: int = Field(ge=1)
    status: Literal[
        "CURRENT", "SUPERSEDED", "EXPIRED", "REVIEW_REQUIRED", "UNKNOWN", "FETCH_FAILED", "EXTRACTION_FAILED"
    ]
    last_checked_at: datetime
    first_retrieved_at: datetime
    extraction_method: str | None = None
    is_ocr: bool


class KnowledgeBaseStatusResponse(BaseModel):
    """Public audit metadata; it never includes source text, hashes, or secrets."""

    generated_at: datetime
    storage: KnowledgeBaseStorageSummary
    sources: list[KnowledgeBaseSourceSummary]
    recent_documents: list[KnowledgeBaseDocumentSummary]


async def _vector_summary(settings: Settings) -> tuple[str, int | None]:
    """Read Qdrant readiness without disclosing or repeatedly probing it."""

    global _vector_summary_cache
    now = datetime.now(UTC)
    cached = _vector_summary_cache
    if cached is not None and (now - cached[0]).total_seconds() < _VECTOR_STATUS_CACHE_SECONDS:
        return cached[1], cached[2]

    async with _vector_summary_lock:
        cached = _vector_summary_cache
        now = datetime.now(UTC)
        if cached is not None and (now - cached[0]).total_seconds() < _VECTOR_STATUS_CACHE_SECONDS:
            return cached[1], cached[2]

        vector_store = QdrantVectorStore(settings)
        if not vector_store.configured:
            result: tuple[str, int | None] = ("not_configured", None)
        else:
            try:
                result = ("connected", await asyncio.to_thread(vector_store.count))
            except VectorStoreError:
                _logger.warning("public_knowledge_vector_status_unavailable")
                result = ("unavailable", None)
        _vector_summary_cache = (now, *result)
        return result


class KnowledgeBaseDocumentListResponse(BaseModel):
    """Paginated document list for mobile app."""
    documents: list[KnowledgeBaseDocumentSummary]
    total: int
    page: int
    limit: int
    has_more: bool


@router.get("", response_model=dict)
async def get_knowledge_base_summary(
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Summary statistics for knowledge base - mobile app compatible."""
    
    client_host = request.client.host if request.client else "unknown"
    _status_limiter.check("public-knowledge-base", client_host)
    snapshot = await KnowledgeRepository(session).admin_dashboard_snapshot()
    vector_status, vector_point_count = await _vector_summary(settings)
    
    return {
        "official_sources": int(snapshot["source_count"]),
        "current_documents": int(snapshot["current_document_count"]),
        "knowledge_chunks": int(snapshot["chunk_count"]),
        "vector_index": vector_status,
    }


@router.get("/documents", response_model=KnowledgeBaseDocumentListResponse)
async def list_knowledge_documents(
    page: int = Query(default=1, ge=1, le=1000),
    limit: int = Query(default=15, ge=1, le=50),
    request: Request = None,  # type: ignore[assignment]
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeBaseDocumentListResponse:
    """Paginated list of knowledge documents for mobile app."""
    
    client_host = request.client.host if request.client else "unknown"
    _status_limiter.check("knowledge-documents", client_host)
    
    snapshot = await KnowledgeRepository(session).admin_dashboard_snapshot()
    all_documents = snapshot["recent_documents"]
    
    # Calculate pagination
    offset = (page - 1) * limit
    total = len(all_documents)
    paginated_docs = all_documents[offset:offset + limit]
    has_more = (offset + limit) < total
    
    return KnowledgeBaseDocumentListResponse(
        documents=[KnowledgeBaseDocumentSummary.model_validate(doc) for doc in paginated_docs],
        total=total,
        page=page,
        limit=limit,
        has_more=has_more,
    )


@router.get("/status", response_model=KnowledgeBaseStatusResponse)
async def get_knowledge_base_status(
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeBaseStatusResponse:
    """Show source provenance and update state without exposing private knowledge data."""

    client_host = request.client.host if request.client else "unknown"
    _status_limiter.check("public-knowledge-base", client_host)
    snapshot = await KnowledgeRepository(session).admin_dashboard_snapshot()
    vector_status, vector_point_count = await _vector_summary(settings)
    safe_sources = []
    for source in snapshot["sources"]:
        source_copy = dict(source)
        latest_check = source_copy.get("latest_check")
        if isinstance(latest_check, dict):
            # Internal failure codes may expose host or provider implementation
            # details. The public page needs outcome counts, not diagnostics.
            source_copy["latest_check"] = {
                key: value for key, value in latest_check.items() if key != "failure_code"
            }
        source_copy.pop("enabled", None)
        safe_sources.append(KnowledgeBaseSourceSummary.model_validate(source_copy))

    return KnowledgeBaseStatusResponse(
        generated_at=datetime.now(UTC),
        storage=KnowledgeBaseStorageSummary(
            vector_index=vector_status,
            vector_point_count=vector_point_count,
            source_count=int(snapshot["source_count"]),
            document_count=int(snapshot["document_count"]),
            current_document_count=int(snapshot["current_document_count"]),
            chunk_count=int(snapshot["chunk_count"]),
        ),
        sources=safe_sources,
        recent_documents=[KnowledgeBaseDocumentSummary.model_validate(item) for item in snapshot["recent_documents"]],
    )
