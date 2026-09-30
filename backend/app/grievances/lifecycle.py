"""Explicit grievance lifecycle rules shared by every mutation path."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from fastapi import HTTPException, status


class GrievanceStatus(StrEnum):
    DRAFT = "DRAFT"
    READY_FOR_CONFIRMATION = "READY_FOR_CONFIRMATION"
    USER_CONFIRMED = "USER_CONFIRMED"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_PROCESS = "UNDER_PROCESS"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"
    APPEAL_AVAILABLE = "APPEAL_AVAILABLE"
    APPEAL_SUBMITTED = "APPEAL_SUBMITTED"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    UNKNOWN = "UNKNOWN"


_ALLOWED_TRANSITIONS: dict[GrievanceStatus, frozenset[GrievanceStatus]] = {
    GrievanceStatus.DRAFT: frozenset({GrievanceStatus.READY_FOR_CONFIRMATION}),
    GrievanceStatus.READY_FOR_CONFIRMATION: frozenset({GrievanceStatus.DRAFT, GrievanceStatus.USER_CONFIRMED}),
    # A portal handoff is not an official submission. The state tells the
    # member that they still need to complete the official portal action.
    GrievanceStatus.USER_CONFIRMED: frozenset({GrievanceStatus.ACTION_REQUIRED}),
    GrievanceStatus.ACTION_REQUIRED: frozenset({GrievanceStatus.ACKNOWLEDGED, GrievanceStatus.UNDER_PROCESS, GrievanceStatus.UNKNOWN}),
    GrievanceStatus.SUBMITTING: frozenset({GrievanceStatus.SUBMITTED, GrievanceStatus.SUBMISSION_FAILED}),
    GrievanceStatus.SUBMITTED: frozenset({GrievanceStatus.ACKNOWLEDGED, GrievanceStatus.UNDER_PROCESS, GrievanceStatus.UNKNOWN}),
    GrievanceStatus.ACKNOWLEDGED: frozenset({GrievanceStatus.UNDER_PROCESS, GrievanceStatus.RESOLVED, GrievanceStatus.CLOSED, GrievanceStatus.ACTION_REQUIRED}),
    GrievanceStatus.UNDER_PROCESS: frozenset({GrievanceStatus.ACTION_REQUIRED, GrievanceStatus.RESOLVED, GrievanceStatus.CLOSED, GrievanceStatus.ESCALATED, GrievanceStatus.APPEAL_AVAILABLE, GrievanceStatus.UNKNOWN}),
    GrievanceStatus.RESOLVED: frozenset({GrievanceStatus.CLOSED, GrievanceStatus.APPEAL_AVAILABLE}),
    GrievanceStatus.CLOSED: frozenset({GrievanceStatus.APPEAL_AVAILABLE}),
    GrievanceStatus.ESCALATED: frozenset({GrievanceStatus.UNDER_PROCESS, GrievanceStatus.CLOSED}),
    GrievanceStatus.APPEAL_AVAILABLE: frozenset({GrievanceStatus.APPEAL_SUBMITTED}),
    GrievanceStatus.APPEAL_SUBMITTED: frozenset({GrievanceStatus.UNDER_PROCESS, GrievanceStatus.CLOSED}),
    GrievanceStatus.SUBMISSION_FAILED: frozenset({GrievanceStatus.DRAFT, GrievanceStatus.READY_FOR_CONFIRMATION}),
    GrievanceStatus.UNKNOWN: frozenset({GrievanceStatus.UNDER_PROCESS, GrievanceStatus.CLOSED, GrievanceStatus.ACTION_REQUIRED}),
}


def now_utc() -> datetime:
    return datetime.now(UTC)


def require_transition(current: str, target: GrievanceStatus) -> None:
    try:
        current_status = GrievanceStatus(current)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This grievance has an invalid lifecycle state.") from error
    if target not in _ALLOWED_TRANSITIONS.get(current_status, frozenset()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That action is not available for the grievance's current state.",
        )
