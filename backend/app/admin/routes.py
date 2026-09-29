"""Admin-only read API for the trusted knowledge-engine operational dashboard."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import (
    clear_admin_session,
    get_current_admin,
    require_admin_csrf,
    set_admin_session,
    verify_admin_credentials,
)
from app.auth.rate_limit import SlidingWindowRateLimiter
from app.auth.session import get_auth_session
from app.config.settings import MissingConfigurationError, Settings, get_settings
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.vectors import QdrantVectorStore, VectorStoreError

router = APIRouter(prefix="/api/admin", tags=["knowledge administration"])
_login_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=300)
_logger = logging.getLogger("sahayak.admin")


class AdminLoginRequest(BaseModel):
    """Bounded credentials submitted to the separate admin login."""

    admin_id: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AdminSessionResponse(BaseModel):
    authenticated: bool


class AdminStorageSummary(BaseModel):
    relational_database: str
    vector_index: str
    vector_point_count: int | None = Field(default=None, ge=0)
    source_count: int = Field(ge=0)
    document_count: int = Field(ge=0)
    current_document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)


class AdminCheckSummary(BaseModel):
    started_at: datetime
    completed_at: datetime | None = None
    result: str
    checked_documents: int = Field(ge=0)
    changed_documents: int = Field(ge=0)
    failure_code: str | None = None


class AdminSourceSummary(BaseModel):
    key: str
    name: str
    category: str
    geographic_scope: str
    approved_domains: list[str]
    entry_urls: list[str]
    enabled: bool
    validation_status: str
    check_interval_hours: int = Field(ge=1)
    last_successful_check_at: datetime | None = None
    last_detected_change_at: datetime | None = None
    last_successful_ingestion_at: datetime | None = None
    current_document_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    latest_check: AdminCheckSummary | None = None


class AdminDocumentSummary(BaseModel):
    source_key: str
    source_name: str
    title: str
    url: str
    version_number: int = Field(ge=1)
    status: str
    last_checked_at: datetime
    first_retrieved_at: datetime
    extraction_method: str | None = None
    is_ocr: bool


class AdminKnowledgeDashboard(BaseModel):
    generated_at: datetime
    storage: AdminStorageSummary
    sources: list[AdminSourceSummary]
    recent_documents: list[AdminDocumentSummary]


@router.post("/session", response_model=AdminSessionResponse)
async def start_admin_session(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> AdminSessionResponse:
    """Start a rate-limited, independent admin session.

    A generic error prevents account enumeration and does not reveal whether an
    ID, password, or dashboard configuration is wrong.
    """

    client_host = request.client.host if request.client else "unknown"
    _login_limiter.check("knowledge-admin", client_host)
    try:
        valid = verify_admin_credentials(
            settings,
            admin_id=payload.admin_id,
            password=payload.password,
        )
    except MissingConfigurationError:
        _logger.error("admin_login_unavailable reason=missing_configuration")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access is not configured.",
        ) from None
    if not valid:
        _logger.warning("admin_login_rejected client=%s", client_host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid administrator credentials.")
    set_admin_session(response, settings=settings)
    _logger.info("admin_login_succeeded client=%s", client_host)
    return AdminSessionResponse(authenticated=True)


@router.get("/session", response_model=AdminSessionResponse)
async def get_admin_session(_: None = Depends(get_current_admin)) -> AdminSessionResponse:
    """Let the single-page UI restore an existing valid admin session."""

    return AdminSessionResponse(authenticated=True)


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def end_admin_session(
    request: Request,
    response: Response,
    _: None = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
) -> None:
    require_admin_csrf(request)
    clear_admin_session(response, settings=settings)


@router.get("/knowledge-dashboard", response_model=AdminKnowledgeDashboard)
async def get_knowledge_dashboard(
    session: AsyncSession = Depends(get_auth_session),
    _: None = Depends(get_current_admin),
    settings: Settings = Depends(get_settings),
) -> AdminKnowledgeDashboard:
    """Expose source/audit metadata, never raw knowledge or provider secrets."""

    snapshot = await KnowledgeRepository(session).admin_dashboard_snapshot()
    vector_status = "not_configured"
    vector_point_count: int | None = None
    vector_store = QdrantVectorStore(settings)
    if vector_store.configured:
        try:
            vector_point_count = await asyncio.to_thread(vector_store.count)
            vector_status = "connected"
        except VectorStoreError:
            vector_status = "unavailable"
            _logger.warning("admin_vector_status_unavailable")

    return AdminKnowledgeDashboard(
        generated_at=datetime.now(UTC),
        storage=AdminStorageSummary(
            relational_database="connected",
            vector_index=vector_status,
            vector_point_count=vector_point_count,
            source_count=int(snapshot["source_count"]),
            document_count=int(snapshot["document_count"]),
            current_document_count=int(snapshot["current_document_count"]),
            chunk_count=int(snapshot["chunk_count"]),
        ),
        sources=[AdminSourceSummary.model_validate(source) for source in snapshot["sources"]],
        recent_documents=[AdminDocumentSummary.model_validate(item) for item in snapshot["recent_documents"]],
    )
