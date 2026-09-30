"""Separate, rate-limited administrator session endpoints."""

from __future__ import annotations

import logging

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
from app.schemes.repository import SchemeRepository

router = APIRouter(prefix="/api/admin", tags=["knowledge administration"])
_login_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=300)
_logger = logging.getLogger("sahayak.admin")


class AdminLoginRequest(BaseModel):
    """Bounded credentials submitted to the separate admin login."""

    admin_id: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AdminSessionResponse(BaseModel):
    authenticated: bool


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


class SchemeSyncResponse(BaseModel):
    """Result of scheme catalog synchronization."""
    
    success: bool
    schemes_updated: int
    message: str


@router.post("/schemes/sync", response_model=SchemeSyncResponse)
async def sync_scheme_catalog(
    request: Request,
    _: None = Depends(get_current_admin),
    session: AsyncSession = Depends(get_auth_session),
) -> SchemeSyncResponse:
    """Manually trigger scheme catalog sync from knowledge base documents.
    
    This backfills scheme records from already-ingested approved documents
    without making any network requests or inventing records.
    """
    require_admin_csrf(request)
    
    try:
        count = await SchemeRepository(session).sync_current_documents()
        _logger.info("admin_scheme_sync_complete changed=%s", count)
        return SchemeSyncResponse(
            success=True,
            schemes_updated=count,
            message=f"Successfully synchronized {count} scheme record(s) from knowledge base."
        )
    except Exception as error:
        _logger.error("admin_scheme_sync_failed", exc_info=True)
        return SchemeSyncResponse(
            success=False,
            schemes_updated=0,
            message=f"Scheme sync failed: {str(error)}"
        )
