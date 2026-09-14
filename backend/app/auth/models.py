"""Small, purpose-built persistence models for Sahayak accounts and OTPs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AuthBase(DeclarativeBase):
    pass


class Account(AuthBase):
    __tablename__ = "sahayak_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(120))
    village_or_town: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(Text)
    user_type: Mapped[str | None] = mapped_column(String(48), index=True)
    cooperative_role: Mapped[str | None] = mapped_column(String(120))
    profile_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class OneTimePasscode(AuthBase):
    __tablename__ = "sahayak_otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
