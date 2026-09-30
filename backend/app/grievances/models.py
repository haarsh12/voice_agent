"""Database records for the Sahayak grievance assistance layer.

The official authority remains the source of truth.  These tables preserve a
member's reviewed draft, route selection, and the history of actions taken in
Sahayak without manufacturing an official registration or status.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import AuthBase


class Grievance(AuthBase):
    __tablename__ = "sahayak_grievances"
    __table_args__ = (
        Index("sahayak_grievances_account_updated_idx", "account_id", "updated_at"),
        Index("sahayak_grievances_account_status_idx", "account_id", "status"),
    )

    # This is Sahayak's public identifier, deliberately distinct from an
    # official acknowledgement number.
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("sahayak_accounts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    original_language: Mapped[str | None] = mapped_column(String(16))
    organization: Mapped[str | None] = mapped_column(String(180))
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(120))
    locality: Mapped[str | None] = mapped_column(String(120))
    incident_date: Mapped[date | None] = mapped_column(Date)
    amount_description: Mapped[str | None] = mapped_column(String(80))
    has_contacted_organization: Mapped[bool | None] = mapped_column()
    prior_reference: Mapped[str | None] = mapped_column(String(120))

    authority_key: Mapped[str | None] = mapped_column(String(64))
    authority_name: Mapped[str | None] = mapped_column(String(180))
    destination_name: Mapped[str | None] = mapped_column(String(180))
    destination_url: Mapped[str | None] = mapped_column(String(500))
    official_tracking_url: Mapped[str | None] = mapped_column(String(500))
    routing_reason: Mapped[str | None] = mapped_column(Text)
    routed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # PORTAL_HANDOFF means no complaint data has been sent by Sahayak.
    submission_method: Mapped[str | None] = mapped_column(String(32))
    official_reference: Mapped[str | None] = mapped_column(String(160))
    official_reference_source: Mapped[str | None] = mapped_column(String(32))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    handoff_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    appeal_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class GrievanceEvent(AuthBase):
    __tablename__ = "sahayak_grievance_events"
    __table_args__ = (Index("sahayak_grievance_events_grievance_time_idx", "grievance_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grievance_id: Mapped[str] = mapped_column(
        ForeignKey("sahayak_grievances.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str | None] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(24), nullable=False)
    # Deliberately stores only non-sensitive operational context. Complaint
    # narrative and document contents never belong in an audit event.
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
