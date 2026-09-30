"""Authenticated grievance APIs; every record query is member scoped."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account
from app.auth.rate_limit import SlidingWindowRateLimiter
from app.auth.security import get_current_account, require_csrf
from app.auth.session import get_auth_session
from app.grievances.lifecycle import GrievanceStatus
from app.grievances.models import Grievance
from app.grievances.schemas import (
    GrievanceConfirmationRequest,
    GrievanceCreateRequest,
    GrievanceListResponse,
    GrievanceReadyRequest,
    GrievanceReferenceRequest,
    GrievanceResponse,
    GrievanceUpdateRequest,
)
from app.grievances.service import (
    confirm,
    count_for_query,
    create_draft,
    get_owned,
    prepare_confirmation,
    record_handoff_opened,
    record_official_reference,
    scoped_list_query,
    serialize,
    update_draft,
)

router = APIRouter(prefix="/api/grievances", tags=["grievances"])
_mutation_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)


def _limit(request: Request, account: Account) -> None:
    client = request.client.host if request.client else "unknown"
    _mutation_limiter.check("grievance", str(account.id), client)


@router.post("", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED)
async def create_grievance(
    payload: GrievanceCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await create_draft(session, account, payload)
    return await serialize(session, grievance)


@router.get("", response_model=GrievanceListResponse)
async def list_grievances(
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    state: GrievanceStatus | None = Query(default=None),
    query: Annotated[str | None, Query(max_length=120)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> GrievanceListResponse:
    statement = scoped_list_query(account.id, status_filter=state, query=query)
    total = await count_for_query(session, statement)
    records = (await session.scalars(statement.order_by(Grievance.updated_at.desc()).offset(offset).limit(limit))).all()
    return GrievanceListResponse(
        items=[await serialize(session, record, include_events=False) for record in records],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{grievance_id}", response_model=GrievanceResponse)
async def get_grievance(
    grievance_id: str,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
) -> GrievanceResponse:
    return await serialize(session, await get_owned(session, account.id, grievance_id))


@router.put("/{grievance_id}", response_model=GrievanceResponse)
async def edit_grievance(
    grievance_id: str,
    payload: GrievanceUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await get_owned(session, account.id, grievance_id)
    await update_draft(session, grievance, payload, expected_version=payload.version)
    return await serialize(session, grievance)


@router.post("/{grievance_id}/ready", response_model=GrievanceResponse)
async def ready_grievance(
    grievance_id: str,
    payload: GrievanceReadyRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await get_owned(session, account.id, grievance_id)
    await prepare_confirmation(session, grievance, expected_version=payload.version)
    return await serialize(session, grievance)


@router.post("/{grievance_id}/confirm", response_model=GrievanceResponse)
async def confirm_grievance(
    grievance_id: str,
    payload: GrievanceConfirmationRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await get_owned(session, account.id, grievance_id)
    await confirm(session, grievance, expected_version=payload.version)
    return await serialize(session, grievance)


@router.post("/{grievance_id}/official-handoff", response_model=GrievanceResponse)
async def open_official_handoff(
    grievance_id: str,
    payload: GrievanceReadyRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await get_owned(session, account.id, grievance_id)
    await record_handoff_opened(session, grievance, expected_version=payload.version)
    return await serialize(session, grievance)


@router.post("/{grievance_id}/official-reference", response_model=GrievanceResponse)
async def add_official_reference(
    grievance_id: str,
    payload: GrievanceReferenceRequest,
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    account: Account = Depends(get_current_account),
    _: None = Depends(require_csrf),
) -> GrievanceResponse:
    _limit(request, account)
    grievance = await get_owned(session, account.id, grievance_id)
    await record_official_reference(
        session, grievance, expected_version=payload.version, official_reference=payload.official_reference
    )
    return await serialize(session, grievance)
