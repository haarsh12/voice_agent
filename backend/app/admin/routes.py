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


class KnowledgeIngestionRequest(BaseModel):
    """Request to ingest knowledge from sources."""
    
    source_key: str | None = Field(default=None, description="Specific source to ingest, or None for all due sources")
    force_all: bool = Field(default=False, description="Force ingestion of all sources regardless of check interval")


class KnowledgeIngestionResponse(BaseModel):
    """Result of knowledge ingestion operation."""
    
    success: bool
    sources_checked: int
    sources_changed: int
    sources_failed: int
    sources_unchanged: int
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class VectorReconcileResponse(BaseModel):
    """Result of vector store reconciliation."""
    
    success: bool
    current_records: int
    repaired_missing: int
    retired_stale: int
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


@router.post("/knowledge/ingest", response_model=KnowledgeIngestionResponse)
async def ingest_knowledge_sources(
    payload: KnowledgeIngestionRequest,
    request: Request,
    _: None = Depends(get_current_admin),
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeIngestionResponse:
    """Manually trigger knowledge source ingestion.
    
    Options:
    - No source_key: Check all sources that are due based on check_interval
    - With source_key: Check specific source immediately
    - With force_all: Force check all registered sources (ignores intervals)
    
    This fetches documents, extracts content, creates embeddings, and stores
    in both PostgreSQL and Qdrant vector store.
    """
    require_admin_csrf(request)
    
    from app.knowledge.ingestion import KnowledgeIngestionService
    from app.knowledge.registry import SOURCES_BY_KEY
    
    try:
        service = KnowledgeIngestionService(session, settings)
        await service.repository.sync_source_registry()
        
        details: dict[str, str] = {}
        
        if payload.force_all:
            # Ingest all registered sources
            _logger.info("admin_knowledge_ingestion_started mode=force_all total=%s", len(SOURCES_BY_KEY))
            
            successful = 0
            failed = 0
            unchanged = 0
            changed = 0
            
            for key, source in sorted(SOURCES_BY_KEY.items()):
                if not source.enabled:
                    details[key] = "SKIPPED_DISABLED"
                    continue
                    
                try:
                    result = await service.check_source(source)
                    details[key] = result.value
                    
                    if result.value == "FAILED":
                        failed += 1
                    elif result.value == "UNCHANGED":
                        unchanged += 1
                    elif result.value in {"CHANGED", "PARTIAL_FAILURE"}:
                        changed += 1
                        successful += 1
                    else:
                        successful += 1
                        
                    _logger.info("admin_source_checked source=%s result=%s", key, result.value)
                except Exception as error:
                    failed += 1
                    details[key] = f"EXCEPTION: {str(error)[:100]}"
                    _logger.error("admin_source_check_failed source=%s", key, exc_info=True)
            
            # Backfill schemes after bulk ingestion
            try:
                scheme_count = await SchemeRepository(session).sync_current_documents()
                _logger.info("admin_scheme_backfill_complete changed=%s", scheme_count)
            except Exception as error:
                _logger.error("admin_scheme_backfill_failed", exc_info=True)
            
            return KnowledgeIngestionResponse(
                success=failed < len(SOURCES_BY_KEY),
                sources_checked=len(SOURCES_BY_KEY),
                sources_changed=changed,
                sources_failed=failed,
                sources_unchanged=unchanged,
                message=f"Bulk ingestion complete: {successful} successful, {failed} failed, {unchanged} unchanged.",
                details=details
            )
            
        elif payload.source_key:
            # Check specific source
            source = SOURCES_BY_KEY.get(payload.source_key)
            if source is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown source key: {payload.source_key}"
                )
            
            _logger.info("admin_knowledge_ingestion_started mode=single_source source=%s", payload.source_key)
            result = await service.check_source(source)
            details[payload.source_key] = result.value
            
            changed = 1 if result.value in {"CHANGED", "PARTIAL_FAILURE"} else 0
            failed = 1 if result.value == "FAILED" else 0
            unchanged = 1 if result.value == "UNCHANGED" else 0
            
            return KnowledgeIngestionResponse(
                success=result.value != "FAILED",
                sources_checked=1,
                sources_changed=changed,
                sources_failed=failed,
                sources_unchanged=unchanged,
                message=f"Source check complete: {result.value}",
                details=details
            )
            
        else:
            # Check only due sources
            _logger.info("admin_knowledge_ingestion_started mode=due_sources")
            results = await service.check_due_sources()
            
            changed = sum(1 for r in results.values() if r.value in {"CHANGED", "PARTIAL_FAILURE"})
            failed = sum(1 for r in results.values() if r.value == "FAILED")
            unchanged = sum(1 for r in results.values() if r.value == "UNCHANGED")
            details = {key: result.value for key, result in results.items()}
            
            return KnowledgeIngestionResponse(
                success=failed < len(results),
                sources_checked=len(results),
                sources_changed=changed,
                sources_failed=failed,
                sources_unchanged=unchanged,
                message=f"Due sources check complete: {len(results)} sources checked.",
                details=details
            )
            
    except Exception as error:
        _logger.error("admin_knowledge_ingestion_failed", exc_info=True)
        return KnowledgeIngestionResponse(
            success=False,
            sources_checked=0,
            sources_changed=0,
            sources_failed=0,
            sources_unchanged=0,
            message=f"Knowledge ingestion failed: {str(error)}",
            details={}
        )


@router.post("/knowledge/reconcile-vectors", response_model=VectorReconcileResponse)
async def reconcile_vector_store(
    request: Request,
    _: None = Depends(get_current_admin),
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> VectorReconcileResponse:
    """Repair missing or stale vectors in Qdrant from PostgreSQL audit store.
    
    This reconciles Qdrant with the authoritative PostgreSQL knowledge base
    without making network requests or re-extracting documents.
    """
    require_admin_csrf(request)
    
    from app.knowledge.ingestion import KnowledgeIngestionService
    
    try:
        service = KnowledgeIngestionService(session, settings)
        await service.repository.sync_source_registry()
        
        _logger.info("admin_vector_reconciliation_started")
        report = await service.reconcile_current_vectors()
        
        return VectorReconcileResponse(
            success=True,
            current_records=report.current_records,
            repaired_missing=report.repaired_missing,
            retired_stale=report.retired_stale,
            message=f"Vector reconciliation complete: {report.repaired_missing} repaired, {report.retired_stale} retired."
        )
        
    except Exception as error:
        _logger.error("admin_vector_reconciliation_failed", exc_info=True)
        return VectorReconcileResponse(
            success=False,
            current_records=0,
            repaired_missing=0,
            retired_stale=0,
            message=f"Vector reconciliation failed: {str(error)}"
        )


@router.get("/knowledge/sources")
async def list_knowledge_sources(
    _: None = Depends(get_current_admin),
) -> dict[str, object]:
    """List all registered knowledge sources with their configuration."""
    
    from app.knowledge.registry import SOURCE_REGISTRY
    
    return {
        "sources": [
            {
                "key": source.key,
                "name": source.name,
                "category": source.category,
                "authority_level": source.authority_level,
                "geographic_scope": source.geographic_scope,
                "check_interval_hours": source.check_interval_hours,
                "enabled": source.enabled,
                "approved_domains": list(source.approved_domains),
                "crawl_target_count": len(source.crawl_targets),
                "expected_categories": list(source.expected_categories),
            }
            for source in SOURCE_REGISTRY
        ],
        "total": len(SOURCE_REGISTRY),
    }

