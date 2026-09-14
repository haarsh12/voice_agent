"""Validation contracts for the Sahayak mobile sign-in and profile flow."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


UserType = Literal[
    "cooperative_member",
    "farmer",
    "pacs_member",
    "cooperative_official",
    "rural_stakeholder",
    "other",
]


def normalise_indian_phone(value: str) -> str:
    cleaned = re.sub(r"[\s()\-]", "", value)
    digits = cleaned[1:] if cleaned.startswith("+") else cleaned
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise ValueError("Enter a valid Indian 10-digit mobile number.")
    return f"+91{digits}"


class OTPRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)
    # None preserves the original endpoint contract for existing integrations.
    # The Sahayak web flow always sends an explicit intent.
    intent: Literal["login", "register"] | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalise_indian_phone(value)


class VerifyOTPRequest(OTPRequest):
    otp_code: str = Field(pattern=r"^\d{6}$")


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=120)
    village_or_town: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=500)
    user_type: UserType | None = None
    cooperative_role: str | None = Field(default=None, max_length=120)

    @field_validator(
        "full_name",
        "state",
        "district",
        "village_or_town",
        "address",
        "cooperative_role",
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned


class ProfileResponse(BaseModel):
    full_name: str | None
    phone_number: str
    state: str | None
    district: str | None
    village_or_town: str | None
    address: str | None
    user_type: UserType | None
    cooperative_role: str | None
    needs_onboarding: bool


class VerifyOTPResponse(ProfileResponse):
    is_new_user: bool
