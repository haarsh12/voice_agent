"""OTP generation, hashing and delivery boundaries. Codes never enter browser logic."""

from __future__ import annotations

import logging
import secrets
import string
from datetime import UTC, datetime, timedelta

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import OneTimePasscode
from app.config.settings import Settings


logger = logging.getLogger("sahayak.auth")
_hasher = PasswordHasher()
OTP_EXPIRY_MINUTES = 5
MAX_VERIFICATION_ATTEMPTS = 5


class OTPDeliveryError(RuntimeError):
    pass


def _new_code(settings: Settings) -> str:
    if settings.otp_demo_mode:
        return settings.require_demo_otp_code()
    return "".join(secrets.choice(string.digits) for _ in range(6))


async def issue_otp(session: AsyncSession, *, phone_number: str, settings: Settings) -> str:
    code = _new_code(settings)
    await session.execute(
        update(OneTimePasscode)
        .where(OneTimePasscode.phone_number == phone_number, OneTimePasscode.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )
    session.add(
        OneTimePasscode(
            phone_number=phone_number,
            code_hash=_hasher.hash(code),
            expires_at=datetime.now(UTC) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )
    )
    await session.commit()
    logger.info("otp_issued phone_tail=%s", phone_number[-4:])
    return code


async def verify_otp(session: AsyncSession, *, phone_number: str, otp_code: str) -> bool:
    code = await session.scalar(
        select(OneTimePasscode)
        .where(
            OneTimePasscode.phone_number == phone_number,
            OneTimePasscode.used_at.is_(None),
            OneTimePasscode.expires_at > datetime.now(UTC),
        )
        .order_by(OneTimePasscode.id.desc())
        .with_for_update()
    )
    if code is None:
        return False
    try:
        is_valid = _hasher.verify(code.code_hash, otp_code)
    except VerificationError:
        is_valid = False
    if is_valid:
        code.used_at = datetime.now(UTC)
    else:
        code.failed_attempts += 1
        if code.failed_attempts >= MAX_VERIFICATION_ATTEMPTS:
            code.used_at = datetime.now(UTC)
    await session.commit()
    return is_valid


async def deliver_otp(*, phone_number: str, code: str, settings: Settings) -> None:
    if settings.otp_demo_mode:
        logger.info("otp_demo_issued phone_tail=%s", phone_number[-4:])
        return
    settings.require_sms_delivery()
    if settings.fast2sms_api_key is None:
        raise OTPDeliveryError("SMS delivery is not configured.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=4.0)) as client:
            response = await client.post(
                settings.fast2sms_base_url,
                headers={"authorization": settings.fast2sms_api_key.get_secret_value()},
                data={
                    "route": "otp",
                    "variables_values": code,
                    "numbers": phone_number[-10:],
                    "flash": "0",
                },
            )
    except httpx.HTTPError as error:
        logger.warning("otp_delivery_transport_error phone_tail=%s", phone_number[-4:])
        raise OTPDeliveryError("OTP delivery is temporarily unavailable.") from error
    if not response.is_success:
        logger.warning("otp_delivery_rejected phone_tail=%s status=%s", phone_number[-4:], response.status_code)
        raise OTPDeliveryError("OTP delivery was rejected.")
