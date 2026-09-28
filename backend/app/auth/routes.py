"""Mobile OTP endpoints and authenticated Sahayak profile endpoints."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account, OneTimePasscode, WebAuthnCeremony, WebAuthnCredential
from app.auth.otp import OTPDeliveryError, deliver_otp, issue_otp, verify_otp
from app.auth.rate_limit import SlidingWindowRateLimiter
from app.auth.schemas import (
    OTPRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    VerifyOTPRequest,
    VerifyOTPResponse,
    WebAuthnAuthenticationFinishRequest,
    WebAuthnOptionsResponse,
    WebAuthnRegistrationFinishRequest,
)
from app.auth.security import (
    clear_session_cookies,
    get_current_account,
    require_csrf,
    set_session_cookies,
)
from app.auth.session import get_auth_session
from app.auth.webauthn import (
    authentication_options,
    new_ceremony_id,
    new_challenge,
    registration_options,
    user_handle_matches_account,
    verify_authentication,
    verify_registration,
)
from app.config.settings import Settings, get_settings


router = APIRouter(prefix="/api/auth", tags=["authentication"])
# Production OTP delivery is deliberately bounded to contain SMS cost and
# automated abuse. The fixed-code local demonstration does not send SMS, so it
# must not lock a person out while they correct profile details or retry the UI.
_request_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=300)
_verify_limiter = SlidingWindowRateLimiter(max_requests=8, window_seconds=300)
_passkey_limiter = SlidingWindowRateLimiter(max_requests=12, window_seconds=300)
_passkey_verify_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=300)
_logger = logging.getLogger(__name__)
_CEREMONY_TTL = timedelta(minutes=5)
_RECENT_OTP_TTL = timedelta(minutes=10)
_MAX_PASSKEYS_PER_ACCOUNT = 5


def _profile_payload(account: Account) -> dict[str, object]:
    return {
        "full_name": account.full_name,
        "phone_number": account.phone_number,
        "state": account.state,
        "district": account.district,
        "village_or_town": account.village_or_town,
        "address": account.address,
        "user_type": account.user_type,
        "cooperative_role": account.cooperative_role,
        "needs_onboarding": not account.profile_completed,
        "face_id_enabled": account.face_id_enabled,
    }


def _web_authn_context(request: Request, settings: Settings) -> tuple[str, str]:
    """Allow a ceremony only from an explicitly trusted configured origin."""

    origin = request.headers.get("origin")
    rp_id = settings.web_authn_rp_id_for_origin(origin)
    if rp_id is None:
        if settings.is_production and not settings.web_authn_rp_id.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Device biometric sign-in is not configured for this site.",
            )
        if not settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Face ID needs a trusted secure Sahayak address. For local testing, "
                    "open the app through http://localhost on its Vite port; use HTTPS for a LAN address."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device biometric sign-in must be started from the Sahayak website.",
        )
    return origin, rp_id


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def _create_ceremony(
    session: AsyncSession,
    *,
    account_id: int | None,
    purpose: str,
    rp_id: str,
    origin: str,
) -> WebAuthnCeremony:
    now = datetime.now(UTC)
    # Challenges are single-use and short-lived. Clearing old records keeps
    # the table bounded without ever retaining a browser biometric response.
    await session.execute(delete(WebAuthnCeremony).where(WebAuthnCeremony.expires_at < now))
    ceremony = WebAuthnCeremony(
        id=new_ceremony_id(),
        account_id=account_id,
        purpose=purpose,
        challenge=new_challenge(),
        rp_id=rp_id,
        origin=origin,
        expires_at=now + _CEREMONY_TTL,
    )
    session.add(ceremony)
    await session.commit()
    return ceremony


async def _claim_ceremony(
    session: AsyncSession,
    *,
    ceremony_id: str,
    purpose: str,
    account_id: int | None,
) -> WebAuthnCeremony:
    ceremony = await session.get(WebAuthnCeremony, ceremony_id)
    if ceremony is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This biometric request has expired. Please try again.")
    account_clause = (
        WebAuthnCeremony.account_id.is_(None)
        if account_id is None
        else WebAuthnCeremony.account_id == account_id
    )
    now = datetime.now(UTC)
    # SQLite does not preserve timezone information for ``DateTime`` values.
    # Bind a matching naïve UTC value there, while PostgreSQL retains the
    # timezone-aware value used in production. Disabling SQLAlchemy's
    # in-memory synchronisation is equally important: otherwise it evaluates
    # this expression against the naïve SQLite object before the query reaches
    # the database and raises a TypeError after the user has created a passkey.
    bind = session.get_bind()
    expiry_cutoff = now.replace(tzinfo=None) if bind.dialect.name == "sqlite" else now
    claimed = await session.execute(
        update(WebAuthnCeremony)
        .where(
            WebAuthnCeremony.id == ceremony_id,
            WebAuthnCeremony.purpose == purpose,
            account_clause,
            WebAuthnCeremony.used_at.is_(None),
            WebAuthnCeremony.expires_at > expiry_cutoff,
        )
        .values(used_at=now)
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    if claimed.rowcount != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This biometric request has expired. Please try again.")
    return ceremony


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
async def request_otp(
    payload: OTPRequest,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    account = await session.scalar(select(Account).where(Account.phone_number == payload.phone_number))
    if payload.intent == "login" and account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="We could not find an account for this mobile number. Choose Create account to get started.",
        )
    if payload.intent == "register" and account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this mobile number. Choose Log in to continue.",
        )
    # Only successful delivery requests consume the limit. This prevents an
    # accidental switch between Log in and Create account from locking a member
    # out. Separate intents keep the two flows independently protected.
    if not settings.otp_demo_mode:
        _request_limiter.check("otp-request", payload.intent or "legacy", payload.phone_number)
    code = await issue_otp(session, phone_number=payload.phone_number, settings=settings)
    try:
        await deliver_otp(phone_number=payload.phone_number, code=code, settings=settings)
    except OTPDeliveryError as error:
        await session.execute(
            update(OneTimePasscode)
            .where(OneTimePasscode.phone_number == payload.phone_number, OneTimePasscode.used_at.is_(None))
            .values(used_at=datetime.now(UTC))
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP delivery is temporarily unavailable. Please try again.",
        ) from error
    return {"message": "OTP sent successfully."}


@router.post("/otp/verify", response_model=VerifyOTPResponse)
async def verify_mobile_otp(
    payload: VerifyOTPRequest,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _verify_limiter.check("otp-verify", payload.phone_number)
    if not await verify_otp(session, phone_number=payload.phone_number, otp_code=payload.otp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The OTP is invalid or has expired.")

    account = await session.scalar(select(Account).where(Account.phone_number == payload.phone_number))
    is_new_user = account is None
    if payload.intent == "login" and account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="We could not find an account for this mobile number. Choose Create account to get started.",
        )
    if payload.intent == "register":
        if account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account already exists for this mobile number. Choose Log in to continue.",
            )
        if payload.registration is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Complete your support profile before verifying your mobile number.",
            )
        account = Account(
            phone_number=payload.phone_number,
            full_name=payload.registration.full_name,
            state=payload.registration.state,
            district=payload.registration.district,
            village_or_town=payload.registration.village_or_town,
            address=payload.registration.address,
            user_type=payload.registration.user_type,
            cooperative_role=payload.registration.cooperative_role,
            profile_completed=True,
            # SQLAlchemy applies column defaults only when it flushes. Set this
            # explicitly because the account is checked before the first flush.
            is_active=True,
        )
    elif account is None:
        # Backwards-compatible path for callers that predate the explicit
        # login/register choice. The web UI always uses the safer paths above.
        # SQLAlchemy's column default has not been applied at this point, but
        # the account must pass the active-account check immediately below.
        account = Account(phone_number=payload.phone_number, is_active=True)

    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is unavailable.")
    if is_new_user:
        session.add(account)
    # A new device credential can only be added immediately after the owner
    # proves control of their verified phone number. A 7-day cookie alone is
    # deliberately not enough to enroll another biometric device.
    account.last_mobile_verification_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(account)
    set_session_cookies(response, account=account, settings=settings)
    return {"is_new_user": is_new_user, **_profile_payload(account)}


@router.post("/face-id/registration/options", response_model=WebAuthnOptionsResponse)
async def begin_face_id_registration(
    request: Request,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Start optional Face ID / device biometric enrollment after OTP proof."""

    require_csrf(request)
    _passkey_limiter.check("passkey-register", str(account.id))
    recent_verification = account.last_mobile_verification_at
    if (
        recent_verification is None
        or _as_utc(recent_verification) < datetime.now(UTC) - _RECENT_OTP_TTL
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="For your security, log in with your mobile OTP again before setting up Face ID.",
        )
    origin, rp_id = _web_authn_context(request, settings)
    credentials = list(
        (await session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.account_id == account.id)
        )).all()
    )
    if len(credentials) >= _MAX_PASSKEYS_PER_ACCOUNT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have reached the limit of five registered devices. Remove Face ID before adding another device.",
        )
    ceremony = await _create_ceremony(
        session,
        account_id=account.id,
        purpose="registration",
        rp_id=rp_id,
        origin=origin,
    )
    return {
        "ceremony_id": ceremony.id,
        "public_key": registration_options(
            account=account,
            credentials=credentials,
            challenge=ceremony.challenge,
            rp_id=rp_id,
            settings=settings,
        ),
    }


@router.post("/face-id/registration/verify", response_model=ProfileResponse)
async def complete_face_id_registration(
    payload: WebAuthnRegistrationFinishRequest,
    request: Request,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_auth_session),
) -> dict[str, object]:
    """Verify and retain only a newly-created public device credential."""

    require_csrf(request)
    _passkey_verify_limiter.check("passkey-register-verify", str(account.id))
    if payload.credential.id != payload.credential.raw_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The device credential is invalid.")
    ceremony = await _claim_ceremony(
        session,
        ceremony_id=payload.ceremony_id,
        purpose="registration",
        account_id=account.id,
    )
    try:
        (
            credential_id,
            public_key,
            sign_count,
            transports,
            device_type,
            backed_up,
        ) = verify_registration(
            credential=payload.credential.model_dump(by_alias=True),
            challenge=ceremony.challenge,
            rp_id=ceremony.rp_id,
            origin=ceremony.origin,
        )
    except Exception:
        # Verification failures intentionally reveal no parser or cryptographic
        # detail. The challenge was already consumed, preventing replay.
        _logger.warning("webauthn_registration_rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="We could not verify this device. Please try Face ID setup again.",
        ) from None
    if credential_id != payload.credential.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The device credential is invalid.")
    if await session.scalar(select(WebAuthnCredential.id).where(WebAuthnCredential.credential_id == credential_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This device is already registered.")
    session.add(
        WebAuthnCredential(
            account_id=account.id,
            credential_id=credential_id,
            credential_public_key=public_key,
            sign_count=sign_count,
            transports=transports,
            device_type=device_type,
            backed_up=backed_up,
        )
    )
    account.face_id_enabled = True
    await session.commit()
    return _profile_payload(account)


@router.post("/face-id/authentication/options", response_model=WebAuthnOptionsResponse)
async def begin_face_id_authentication(
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Start usernameless biometric sign-in without disclosing account data."""

    origin, rp_id = _web_authn_context(request, settings)
    client_key = request.client.host if request.client else "unknown"
    _passkey_limiter.check("passkey-login", client_key, rp_id)
    ceremony = await _create_ceremony(
        session,
        account_id=None,
        purpose="authentication",
        rp_id=rp_id,
        origin=origin,
    )
    return {
        "ceremony_id": ceremony.id,
        "public_key": authentication_options(challenge=ceremony.challenge, rp_id=rp_id),
    }


@router.post("/face-id/authentication/verify", response_model=ProfileResponse)
async def complete_face_id_authentication(
    payload: WebAuthnAuthenticationFinishRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Verify one signature and issue the ordinary Sahayak session cookie."""

    client_key = request.client.host if request.client else "unknown"
    _passkey_verify_limiter.check("passkey-login-verify", client_key)
    if payload.credential.id != payload.credential.raw_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The device credential is invalid.")
    ceremony = await _claim_ceremony(
        session,
        ceremony_id=payload.ceremony_id,
        purpose="authentication",
        account_id=None,
    )
    stored_credential = await session.scalar(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == payload.credential.id)
    )
    if stored_credential is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="We could not identify this device.")
    account = await session.get(Account, stored_credential.account_id)
    if account is None or not account.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This account is unavailable.")
    if not user_handle_matches_account(payload.credential.response.user_handle, account):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="We could not verify this device.")
    try:
        sign_count, device_type, backed_up = verify_authentication(
            credential=payload.credential.model_dump(by_alias=True),
            challenge=ceremony.challenge,
            rp_id=ceremony.rp_id,
            origin=ceremony.origin,
            stored_credential=stored_credential,
        )
    except Exception:
        _logger.warning("webauthn_authentication_rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face ID did not match. Try again or use your mobile OTP.",
        ) from None
    stored_credential.sign_count = sign_count
    stored_credential.device_type = device_type
    stored_credential.backed_up = backed_up
    stored_credential.last_used_at = datetime.now(UTC)
    await session.commit()
    set_session_cookies(response, account=account, settings=settings)
    return _profile_payload(account)


@router.delete("/face-id", response_model=ProfileResponse)
async def remove_face_id(
    request: Request,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_auth_session),
) -> dict[str, object]:
    """Remove all device biometric credentials for the signed-in member."""

    require_csrf(request)
    await session.execute(delete(WebAuthnCredential).where(WebAuthnCredential.account_id == account.id))
    account.face_id_enabled = False
    await session.commit()
    return _profile_payload(account)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(account: Account = Depends(get_current_account)) -> dict[str, object]:
    return _profile_payload(account)


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_auth_session),
) -> dict[str, object]:
    require_csrf(request)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    account.profile_completed = all(
        value is not None and bool(str(value).strip())
        for value in (account.full_name, account.state, account.district, account.village_or_town, account.user_type)
    )
    await session.commit()
    await session.refresh(account)
    return _profile_payload(account)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    account: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> None:
    require_csrf(request)
    account.token_version += 1
    await session.commit()
    clear_session_cookies(response, settings=settings)
