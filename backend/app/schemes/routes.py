"""Public, read-only scheme catalogue APIs backed by approved evidence."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_optional_current_account
from app.auth.session import get_auth_session
from app.config.settings import Settings, get_settings
from app.schemes.contracts import SchemeDetail, SchemeSearchPage, SchemeSummary
from app.schemes.repository import SchemeRepository

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


class SchemeSummaryResponse(BaseModel):
    id: str
    slug: str
    official_name: str
    short_name: str | None
    scheme_type: str
    category: str
    description: str | None
    beneficiary_categories: list[str]
    relevant_user_types: list[str]
    applicable_states: list[str]
    applicable_districts: list[str]
    geographic_scope: str
    status: str
    verification_status: str
    last_checked_at: datetime


class SchemeSourceResponse(BaseModel):
    source_name: str
    title: str
    # Sahayak's UI shows this as provenance, never an external action.
    url: str
    relevant_section: str | None
    page_number: int | None
    document_version: int | None


class SchemeDetailResponse(SchemeSummaryResponse):
    data: dict[str, object]
    sources: list[SchemeSourceResponse]
    current_version_number: int | None


class SchemeSearchResponse(BaseModel):
    items: list[SchemeSummaryResponse] = Field(default_factory=list)
    total: int
    offset: int
    limit: int


class SchemeFilterResponse(BaseModel):
    categories: list[str]
    beneficiaries: list[str]
    states: list[str]
    types: list[str]


async def _profile_context(request: Request, session: AsyncSession, settings: Settings) -> tuple[str | None, str | None, str | None]:
    account = await get_optional_current_account(request, session, settings)
    return (account.user_type, account.state, account.district) if account is not None else (None, None, None)


@router.get("", response_model=SchemeSearchResponse)
async def list_schemes(
    request: Request,
    query: str | None = Query(default=None, max_length=240),
    category: str | None = Query(default=None, max_length=96),
    beneficiary: str | None = Query(default=None, max_length=48),
    state: str | None = Query(default=None, max_length=100),
    district: str | None = Query(default=None, max_length=120),
    relevant_to_me: bool = False,
    active_only: bool = False,
    limit: int = Query(default=18, ge=1, le=48),
    offset: int = Query(default=0, ge=0, le=10000),
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> SchemeSearchResponse:
    """Search the bounded catalogue. This user-facing path never crawls."""

    profile_type, profile_state, profile_district = await _profile_context(request, session, settings)
    if relevant_to_me:
        beneficiary, state, district = profile_type or beneficiary, profile_state or state, profile_district or district
    page = await SchemeRepository(session).list_schemes(
        query=query,
        category=category,
        beneficiary=beneficiary,
        state=state,
        district=district,
        include_unknown_status=not active_only,
        limit=limit,
        offset=offset,
    )
    return _page_response(page)


@router.get("/filters", response_model=SchemeFilterResponse)
async def scheme_filters(session: AsyncSession = Depends(get_auth_session)) -> SchemeFilterResponse:
    return SchemeFilterResponse(**(await SchemeRepository(session).filter_options()))


@router.get("/{identifier}", response_model=SchemeDetailResponse)
async def scheme_detail(identifier: str, session: AsyncSession = Depends(get_auth_session)) -> SchemeDetailResponse:
    if len(identifier) > 180:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheme not found.")
    item = await SchemeRepository(session).get_scheme(identifier)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheme not found.")
    return _detail_response(item)


def _summary_response(item: SchemeSummary) -> SchemeSummaryResponse:
    return SchemeSummaryResponse(
        id=item.id, slug=item.slug, official_name=item.official_name, short_name=item.short_name,
        scheme_type=item.scheme_type, category=item.category, description=item.description,
        beneficiary_categories=list(item.beneficiary_categories), relevant_user_types=list(item.relevant_user_types),
        applicable_states=list(item.applicable_states), applicable_districts=list(item.applicable_districts),
        geographic_scope=item.geographic_scope, status=item.status.value,
        verification_status=item.verification_status.value, last_checked_at=item.last_checked_at,
    )


def _page_response(page: SchemeSearchPage) -> SchemeSearchResponse:
    return SchemeSearchResponse(items=[_summary_response(item) for item in page.items], total=page.total, offset=page.offset, limit=page.limit)


def _detail_response(item: SchemeDetail) -> SchemeDetailResponse:
    return SchemeDetailResponse(
        **_summary_response(item).model_dump(),
        data=item.data,
        sources=[
            SchemeSourceResponse(
                source_name=source.source_name, title=source.title, url=source.url,
                relevant_section=source.relevant_section, page_number=source.page_number,
                document_version=source.document_version,
            )
            for source in item.sources
        ],
        current_version_number=item.current_version_number,
    )
