"""Validation contracts for the Sahayak mobile sign-in and profile flow."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class RegistrationProfile(BaseModel):
    """The information collected before a new account's phone verification."""

    full_name: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=120)
    village_or_town: str = Field(min_length=2, max_length=120)
    user_type: UserType
    address: str | None = Field(default=None, max_length=500)
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
    def strip_registration_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned


class VerifyOTPRequest(OTPRequest):
    otp_code: str = Field(pattern=r"^\d{6}$")
    registration: RegistrationProfile | None = None


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
    face_id_enabled: bool


class VerifyOTPResponse(ProfileResponse):
    is_new_user: bool


class WebAuthnOptionsResponse(BaseModel):
    ceremony_id: str
    public_key: dict[str, Any]


class _WebAuthnPayload(BaseModel):
    """Strictly bounded JSON returned by the browser WebAuthn APIs."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str = Field(min_length=16, max_length=1024, pattern=r"^[A-Za-z0-9_-]+$")
    raw_id: str = Field(min_length=16, max_length=1024, alias="rawId", pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["public-key"]
    client_extension_results: dict[str, Any] = Field(
        default_factory=dict, alias="clientExtensionResults"
    )
    authenticator_attachment: Literal["platform", "cross-platform"] | None = Field(
        default=None, alias="authenticatorAttachment"
    )

    @field_validator("id", "raw_id")
    @classmethod
    def matching_credential_ids(cls, value: str) -> str:
        return value


class WebAuthnRegistrationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_data_json: str = Field(
        min_length=16, max_length=16_384, alias="clientDataJSON", pattern=r"^[A-Za-z0-9_-]+$"
    )
    attestation_object: str = Field(
        min_length=16, max_length=65_536, alias="attestationObject", pattern=r"^[A-Za-z0-9_-]+$"
    )
    transports: list[Literal["usb", "nfc", "ble", "internal", "hybrid", "smart-card"]] = Field(
        default_factory=list, max_length=6
    )


class WebAuthnRegistrationCredential(_WebAuthnPayload):
    response: WebAuthnRegistrationResponse


class WebAuthnAuthenticationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_data_json: str = Field(
        min_length=16, max_length=16_384, alias="clientDataJSON", pattern=r"^[A-Za-z0-9_-]+$"
    )
    authenticator_data: str = Field(
        min_length=16, max_length=16_384, alias="authenticatorData", pattern=r"^[A-Za-z0-9_-]+$"
    )
    signature: str = Field(min_length=16, max_length=16_384, pattern=r"^[A-Za-z0-9_-]+$")
    user_handle: str | None = Field(
        default=None, max_length=1024, alias="userHandle", pattern=r"^[A-Za-z0-9_-]+$"
    )


class WebAuthnAuthenticationCredential(_WebAuthnPayload):
    response: WebAuthnAuthenticationResponse


class WebAuthnRegistrationFinishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ceremony_id: str = Field(min_length=32, max_length=96, pattern=r"^[A-Za-z0-9_-]+$")
    credential: WebAuthnRegistrationCredential


class WebAuthnAuthenticationFinishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ceremony_id: str = Field(min_length=32, max_length=96, pattern=r"^[A-Za-z0-9_-]+$")
    credential: WebAuthnAuthenticationCredential
