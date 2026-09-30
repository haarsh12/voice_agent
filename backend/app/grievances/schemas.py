"""Bounded API contracts for grievance records."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.grievances.lifecycle import GrievanceStatus
from app.grievances.routing import GrievanceCategory

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(_CONTROL_CHARACTERS.sub(" ", value).split()).strip()
    return cleaned or None


class GrievanceDraftInput(BaseModel):
    """Editable factual fields. All optional fields support progressive collection."""

    model_config = ConfigDict(extra="forbid")

    category: GrievanceCategory | None = None
    subject: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=6_000)
    original_language: str | None = Field(default=None, max_length=16)
    organization: str | None = Field(default=None, max_length=180)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=120)
    locality: str | None = Field(default=None, max_length=120)
    incident_date: date | None = None
    amount_description: str | None = Field(default=None, max_length=80)
    has_contacted_organization: bool | None = None
    prior_reference: str | None = Field(default=None, max_length=120)

    @field_validator(
        "subject", "description", "original_language", "organization", "state", "district",
        "locality", "amount_description", "prior_reference",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return _clean_optional(value)


class GrievanceCreateRequest(GrievanceDraftInput):
    pass


class GrievanceUpdateRequest(GrievanceDraftInput):
    version: Annotated[int, Field(ge=1)]


class GrievanceReadyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Annotated[int, Field(ge=1)]


class GrievanceConfirmationRequest(BaseModel):
    """A literal true prevents accidental/ambiguous confirmation payloads."""

    model_config = ConfigDict(extra="forbid")
    version: Annotated[int, Field(ge=1)]
    confirmed: Literal[True]


class GrievanceReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Annotated[int, Field(ge=1)]
    official_reference: str = Field(min_length=1, max_length=160)

    @field_validator("official_reference")
    @classmethod
    def clean_reference(cls, value: str) -> str:
        cleaned = _clean_optional(value)
        if not cleaned:
            raise ValueError("Enter the acknowledgement number exactly as provided.")
        return cleaned


class GrievanceEventResponse(BaseModel):
    event_type: str
    from_status: GrievanceStatus | None
    to_status: GrievanceStatus | None
    actor: str
    created_at: datetime
    message: str


class GrievanceResponse(BaseModel):
    id: str
    status: GrievanceStatus
    category: GrievanceCategory
    subject: str | None
    description: str | None
    original_language: str | None
    organization: str | None
    state: str | None
    district: str | None
    locality: str | None
    incident_date: date | None
    amount_description: str | None
    has_contacted_organization: bool | None
    prior_reference: str | None
    authority_name: str | None
    destination_name: str | None
    destination_url: str | None
    official_tracking_url: str | None
    routing_reason: str | None
    submission_method: str | None
    official_reference: str | None
    official_reference_source: str | None
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None
    handoff_opened_at: datetime | None
    submitted_at: datetime | None
    acknowledged_at: datetime | None
    last_status_checked_at: datetime | None
    status_changed_at: datetime
    version: int
    missing_fields: list[str]
    events: list[GrievanceEventResponse] = Field(default_factory=list)


class GrievanceListResponse(BaseModel):
    items: list[GrievanceResponse]
    total: int
    offset: int
    limit: int
