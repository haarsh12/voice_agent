"""Lifecycle operations for grievance drafts and official portal handoff."""

from __future__ import annotations

import secrets
from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account
from app.grievances.lifecycle import GrievanceStatus, now_utc, require_transition
from app.grievances.models import Grievance, GrievanceEvent
from app.grievances.routing import GrievanceCategory, classify_statement, route_for
from app.grievances.schemas import (
    GrievanceDraftInput,
    GrievanceEventResponse,
    GrievanceResponse,
)

_EDITABLE_STATUSES = {GrievanceStatus.DRAFT.value, GrievanceStatus.READY_FOR_CONFIRMATION.value}

_EVENT_MESSAGES = {
    "CREATED": "Grievance draft created",
    "UPDATED": "Grievance details updated",
    "ROUTED": "Verified handoff route prepared",
    "READY": "Grievance preview ready for your confirmation",
    "CONFIRMED": "You confirmed the reviewed grievance",
    "HANDOFF_OPENED": "Official grievance portal opened",
    "OFFICIAL_REFERENCE_RECORDED": "Official reference recorded from the member",
}


def _new_id() -> str:
    # Random internal public ID; never formatted to resemble a government ID.
    return "SAH-GRV-" + secrets.token_hex(6).upper()


def missing_fields(grievance: Grievance) -> list[str]:
    required: list[tuple[str, object]] = [
        ("a short subject", grievance.subject),
        ("what happened", grievance.description),
        ("your state", grievance.state),
    ]
    if grievance.category in {GrievanceCategory.PACS.value, GrievanceCategory.COOPERATIVE.value, GrievanceCategory.PAYMENT.value, GrievanceCategory.LOAN.value}:
        required.append(("the organisation or PACS involved", grievance.organization))
    return [label for label, value in required if value is None or value == ""]


def _event(
    grievance: Grievance,
    *,
    event_type: str,
    actor: str,
    from_status: str | None = None,
    to_status: str | None = None,
    metadata: dict[str, object] | None = None,
) -> GrievanceEvent:
    return GrievanceEvent(
        grievance_id=grievance.id,
        event_type=event_type,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
        metadata_json=metadata or {},
    )


def _apply_fields(grievance: Grievance, payload: GrievanceDraftInput, *, only_set: set[str] | None = None) -> None:
    fields = (
        "category", "subject", "description", "original_language", "organization", "state",
        "district", "locality", "incident_date", "amount_description", "has_contacted_organization",
        "prior_reference",
    )
    values = payload.model_dump(exclude_unset=True)
    for field in fields:
        if field in values and (only_set is None or field in only_set):
            value = values[field]
            # Category always has a safe, explicit fallback. A client may use
            # null to mean "please classify this" during draft creation, but
            # a persisted grievance must never lose its category invariant.
            if field == "category" and value is None:
                continue
            setattr(grievance, field, value.value if isinstance(value, GrievanceCategory) else value)


def _apply_route(grievance: Grievance) -> None:
    route = route_for(GrievanceCategory(grievance.category))
    grievance.authority_key = route.key
    grievance.authority_name = route.authority_name
    grievance.destination_name = route.destination_name
    grievance.destination_url = route.destination_url
    grievance.official_tracking_url = route.tracking_url
    grievance.routing_reason = route.reason
    grievance.routed_at = now_utc()
    grievance.submission_method = "PORTAL_HANDOFF"


def _transition(grievance: Grievance, target: GrievanceStatus) -> tuple[str, str]:
    previous = grievance.status
    require_transition(previous, target)
    timestamp = now_utc()
    grievance.status = target.value
    grievance.status_changed_at = timestamp
    if target is GrievanceStatus.USER_CONFIRMED:
        grievance.confirmed_at = timestamp
    if target is GrievanceStatus.ACTION_REQUIRED:
        grievance.handoff_opened_at = timestamp
    if target is GrievanceStatus.ACKNOWLEDGED:
        grievance.acknowledged_at = timestamp
    return previous, target.value


async def create_draft(session: AsyncSession, account: Account, payload: GrievanceDraftInput) -> Grievance:
    category = payload.category
    if category is None and payload.description:
        category = classify_statement(payload.description)
    grievance = Grievance(
        id=_new_id(),
        account_id=account.id,
        status=GrievanceStatus.DRAFT.value,
        category=(category or GrievanceCategory.OTHER).value,
        status_changed_at=now_utc(),
    )
    _apply_fields(grievance, payload)
    _apply_route(grievance)
    session.add(grievance)
    session.add(_event(grievance, event_type="CREATED", actor="MEMBER", to_status=grievance.status))
    session.add(_event(grievance, event_type="ROUTED", actor="SYSTEM", metadata={"route": grievance.authority_key or ""}))
    await session.commit()
    await session.refresh(grievance)  # Refresh to ensure object is attached after commit
    return grievance


async def get_owned(session: AsyncSession, account_id: int, grievance_id: str) -> Grievance:
    grievance = await session.scalar(
        select(Grievance).where(Grievance.id == grievance_id, Grievance.account_id == account_id)
    )
    if grievance is None:
        # Do not reveal whether another member's ID exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found.")
    return grievance


async def update_draft(
    session: AsyncSession, grievance: Grievance, payload: GrievanceDraftInput, *, expected_version: int
) -> Grievance:
    if grievance.status not in _EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This grievance can no longer be edited.")
    _require_version(grievance, expected_version)
    before_category = grievance.category
    _apply_fields(grievance, payload)
    if grievance.category != before_category or any(
        field in payload.model_fields_set for field in {"state", "district", "organization"}
    ):
        _apply_route(grievance)
        session.add(_event(grievance, event_type="ROUTED", actor="SYSTEM", metadata={"route": grievance.authority_key or ""}))
    if grievance.status == GrievanceStatus.READY_FOR_CONFIRMATION.value:
        old, new = _transition(grievance, GrievanceStatus.DRAFT)
        session.add(_event(grievance, event_type="UPDATED", actor="MEMBER", from_status=old, to_status=new))
    else:
        session.add(_event(grievance, event_type="UPDATED", actor="MEMBER"))
    grievance.version += 1
    await session.commit()
    await session.refresh(grievance)  # Refresh to ensure object is attached after commit
    return grievance


async def prepare_confirmation(session: AsyncSession, grievance: Grievance, *, expected_version: int) -> Grievance:
    _require_version(grievance, expected_version)
    if grievance.status != GrievanceStatus.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review is not available for this grievance right now.")
    missing = missing_fields(grievance)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Add " + ", ".join(missing) + " before reviewing this grievance.",
        )
    _apply_route(grievance)
    old, new = _transition(grievance, GrievanceStatus.READY_FOR_CONFIRMATION)
    grievance.version += 1
    session.add(_event(grievance, event_type="READY", actor="SYSTEM", from_status=old, to_status=new))
    await session.commit()
    await session.refresh(grievance)  # Refresh to ensure object is attached after commit
    return grievance


async def confirm(session: AsyncSession, grievance: Grievance, *, expected_version: int) -> Grievance:
    _require_version(grievance, expected_version)
    if grievance.status != GrievanceStatus.READY_FOR_CONFIRMATION.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review the grievance before confirming it.")
    old, new = _transition(grievance, GrievanceStatus.USER_CONFIRMED)
    grievance.version += 1
    session.add(_event(grievance, event_type="CONFIRMED", actor="MEMBER", from_status=old, to_status=new))
    await session.commit()
    await session.refresh(grievance)  # Refresh to ensure object is attached after commit
    return grievance


async def record_handoff_opened(session: AsyncSession, grievance: Grievance, *, expected_version: int) -> Grievance:
    _require_version(grievance, expected_version)
    if grievance.status == GrievanceStatus.USER_CONFIRMED.value:
        old, new = _transition(grievance, GrievanceStatus.ACTION_REQUIRED)
    elif grievance.status == GrievanceStatus.ACTION_REQUIRED.value:
        old, new = grievance.status, grievance.status
        grievance.handoff_opened_at = now_utc()
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Confirm the grievance before opening the official portal.")
    grievance.version += 1
    session.add(_event(grievance, event_type="HANDOFF_OPENED", actor="MEMBER", from_status=old, to_status=new))
    await session.commit()
    return grievance


async def record_official_reference(
    session: AsyncSession, grievance: Grievance, *, expected_version: int, official_reference: str
) -> Grievance:
    _require_version(grievance, expected_version)
    if grievance.status not in {GrievanceStatus.ACTION_REQUIRED.value, GrievanceStatus.ACKNOWLEDGED.value}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Open the official portal before recording an acknowledgement.")
    old, new = (grievance.status, grievance.status)
    if grievance.status == GrievanceStatus.ACTION_REQUIRED.value:
        old, new = _transition(grievance, GrievanceStatus.ACKNOWLEDGED)
    grievance.official_reference = official_reference
    grievance.official_reference_source = "MEMBER_REPORTED"
    grievance.version += 1
    session.add(_event(
        grievance,
        event_type="OFFICIAL_REFERENCE_RECORDED",
        actor="MEMBER",
        from_status=old,
        to_status=new,
        metadata={"source": "MEMBER_REPORTED"},
    ))
    await session.commit()
    return grievance


def _require_version(grievance: Grievance, expected_version: int) -> None:
    if grievance.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This grievance changed in another session. Refresh it before trying again.",
        )


async def serialize(session: AsyncSession, grievance: Grievance, *, include_events: bool = True) -> GrievanceResponse:
    events: Iterable[GrievanceEvent] = ()
    if include_events:
        events = (await session.scalars(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == grievance.id)
            .order_by(GrievanceEvent.created_at.asc(), GrievanceEvent.id.asc())
        )).all()
    return GrievanceResponse(
        id=grievance.id,
        status=GrievanceStatus(grievance.status),
        category=GrievanceCategory(grievance.category),
        subject=grievance.subject,
        description=grievance.description,
        original_language=grievance.original_language,
        organization=grievance.organization,
        state=grievance.state,
        district=grievance.district,
        locality=grievance.locality,
        incident_date=grievance.incident_date,
        amount_description=grievance.amount_description,
        has_contacted_organization=grievance.has_contacted_organization,
        prior_reference=grievance.prior_reference,
        authority_name=grievance.authority_name,
        destination_name=grievance.destination_name,
        destination_url=grievance.destination_url,
        official_tracking_url=grievance.official_tracking_url,
        routing_reason=grievance.routing_reason,
        submission_method=grievance.submission_method,
        official_reference=grievance.official_reference,
        official_reference_source=grievance.official_reference_source,
        created_at=grievance.created_at,
        updated_at=grievance.updated_at,
        confirmed_at=grievance.confirmed_at,
        handoff_opened_at=grievance.handoff_opened_at,
        submitted_at=grievance.submitted_at,
        acknowledged_at=grievance.acknowledged_at,
        last_status_checked_at=grievance.last_status_checked_at,
        status_changed_at=grievance.status_changed_at,
        version=grievance.version,
        missing_fields=missing_fields(grievance),
        events=[
            GrievanceEventResponse(
                event_type=event.event_type,
                from_status=GrievanceStatus(event.from_status) if event.from_status else None,
                to_status=GrievanceStatus(event.to_status) if event.to_status else None,
                actor=event.actor,
                created_at=event.created_at,
                message=_EVENT_MESSAGES.get(event.event_type, "Grievance updated"),
            )
            for event in events
        ],
    )


def scoped_list_query(account_id: int, *, status_filter: GrievanceStatus | None, query: str | None) -> Select[tuple[Grievance]]:
    statement = select(Grievance).where(Grievance.account_id == account_id)
    if status_filter is not None:
        statement = statement.where(Grievance.status == status_filter.value)
    if query:
        safe = query.strip()[:120]
        if safe:
            statement = statement.where(
                Grievance.subject.ilike(f"%{safe}%") | Grievance.official_reference.ilike(f"%{safe}%") | Grievance.id.ilike(f"%{safe}%")
            )
    return statement


async def count_for_query(session: AsyncSession, statement: Select[tuple[Grievance]]) -> int:
    return int(await session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
