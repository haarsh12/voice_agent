"""Mobile OTP endpoints and authenticated Sahayak profile endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account, OneTimePasscode
from app.auth.otp import OTPDeliveryError, deliver_otp, issue_otp, verify_otp
from app.auth.rate_limit import SlidingWindowRateLimiter
from app.auth.schemas import OTPRequest, ProfileResponse, ProfileUpdateRequest, VerifyOTPRequest, VerifyOTPResponse
from app.auth.security import (
    clear_session_cookies,
    get_current_account,
    require_csrf,
    set_session_cookies,
)
from app.auth.session import get_auth_session
from app.config.settings import Settings, get_settings


router = APIRouter(prefix="/api/auth", tags=["authentication"])
_request_limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=300)
_verify_limiter = SlidingWindowRateLimiter(max_requests=8, window_seconds=300)


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
    }


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
async def request_otp(
    payload: OTPRequest,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    _request_limiter.check("otp-request", payload.phone_number)
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
    if account is None:
        account = Account(phone_number=payload.phone_number)
        session.add(account)
        await session.commit()
        await session.refresh(account)
    if not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is unavailable.")
    set_session_cookies(response, account=account, settings=settings)
    return {"is_new_user": is_new_user, **_profile_payload(account)}


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
