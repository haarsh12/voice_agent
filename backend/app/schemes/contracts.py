"""Typed, display-safe contracts for the canonical scheme catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SchemeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UPCOMING = "UPCOMING"
    APPLICATION_OPEN = "APPLICATION_OPEN"
    APPLICATION_CLOSED = "APPLICATION_CLOSED"
    PAUSED = "PAUSED"
    SUPERSEDED = "SUPERSEDED"
    DISCONTINUED = "DISCONTINUED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class SchemeVerificationStatus(str, Enum):
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class SchemeSourceReference:
    source_name: str
    title: str
    url: str
    relevant_section: str | None
    page_number: int | None
    document_version: int | None


@dataclass(frozen=True)
class SchemeSummary:
    id: str
    slug: str
    official_name: str
    short_name: str | None
    scheme_type: str
    category: str
    description: str | None
    beneficiary_categories: tuple[str, ...]
    relevant_user_types: tuple[str, ...]
    applicable_states: tuple[str, ...]
    applicable_districts: tuple[str, ...]
    geographic_scope: str
    status: SchemeStatus
    verification_status: SchemeVerificationStatus
    last_checked_at: datetime


@dataclass(frozen=True)
class SchemeDetail(SchemeSummary):
    data: dict[str, object]
    sources: tuple[SchemeSourceReference, ...]
    current_version_number: int | None


@dataclass(frozen=True)
class SchemeSearchPage:
    items: tuple[SchemeSummary, ...]
    total: int
    offset: int
    limit: int

