"""Server-side WebAuthn helpers for device biometric sign-in.

WebAuthn delegates biometric matching to the operating system. Sahayak stores
only a public credential and a signature counter, never a face scan, image,
embedding, template, or private key.
"""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any

from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.auth.models import Account, WebAuthnCredential
from app.config.settings import Settings


def new_ceremony_id() -> str:
    return secrets.token_urlsafe(48)


def new_challenge() -> str:
    return secrets.token_urlsafe(32)


def registration_options(
    *,
    account: Account,
    credentials: list[WebAuthnCredential],
    challenge: str,
    rp_id: str,
    settings: Settings,
) -> dict[str, Any]:
    """Create a platform, discoverable credential registration challenge."""

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=settings.web_authn_rp_name,
        user_id=str(account.id).encode("utf-8"),
        user_name=account.phone_number,
        user_display_name=account.full_name or "Sahayak member",
        challenge=base64url_to_bytes(challenge),
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id))
            for item in credentials
        ],
    )
    return json.loads(options_to_json(options))


def authentication_options(*, challenge: str, rp_id: str) -> dict[str, Any]:
    """Create a usernameless challenge so a passkey identifies its account."""

    options = generate_authentication_options(
        rp_id=rp_id,
        challenge=base64url_to_bytes(challenge),
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return json.loads(options_to_json(options))


def verify_registration(
    *,
    credential: dict[str, Any],
    challenge: str,
    rp_id: str,
    origin: str,
) -> tuple[str, str, int, str | None, str | None, bool]:
    """Verify enrollment and return only the public values safe to persist."""

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(challenge),
        expected_rp_id=rp_id,
        expected_origin=origin,
        require_user_verification=True,
    )
    transports = credential.get("response", {}).get("transports", [])
    return (
        _bytes_to_base64url(verification.credential_id),
        _bytes_to_base64url(verification.credential_public_key),
        verification.sign_count,
        ",".join(transports) or None,
        _enum_value(verification.credential_device_type),
        bool(verification.credential_backed_up),
    )


def verify_authentication(
    *,
    credential: dict[str, Any],
    challenge: str,
    rp_id: str,
    origin: str,
    stored_credential: WebAuthnCredential,
) -> tuple[int, str | None, bool]:
    """Verify one assertion against its stored public key and counter."""

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(challenge),
        expected_rp_id=rp_id,
        expected_origin=origin,
        credential_public_key=base64url_to_bytes(stored_credential.credential_public_key),
        credential_current_sign_count=stored_credential.sign_count,
        require_user_verification=True,
    )
    return (
        verification.new_sign_count,
        _enum_value(verification.credential_device_type),
        bool(verification.credential_backed_up),
    )


def user_handle_matches_account(user_handle: str | None, account: Account) -> bool:
    """Bind a discoverable credential's optional returned handle to its owner."""

    if user_handle is None:
        return True
    try:
        return base64url_to_bytes(user_handle) == str(account.id).encode("utf-8")
    except ValueError:
        return False


def _bytes_to_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    candidate = getattr(value, "value", value)
    return str(candidate)
