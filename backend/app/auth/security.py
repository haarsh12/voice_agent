"""JWT issuance and cookie/bearer validation owned exclusively by FastAPI."""

from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account
from app.auth.session import get_auth_session
from app.config.settings import Settings, get_settings


ALGORITHM = "HS256"
SESSION_COOKIE = "sahayak_session"
CSRF_COOKIE = "sahayak_csrf"
CSRF_HEADER = "X-Sahayak-CSRF"


def create_access_token(account: Account, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_minutes)
    return jwt.encode(
        {"sub": str(account.id), "tv": account.token_version, "exp": expires_at},
        settings.require_jwt_secret(),
        algorithm=ALGORITHM,
    )


def _decode_access_token(token: str, settings: Settings) -> tuple[int, int] | None:
    try:
        claims = jwt.decode(token, settings.require_jwt_secret(), algorithms=[ALGORITHM])
        return int(claims["sub"]), int(claims["tv"])
    except (JWTError, KeyError, TypeError, ValueError, RuntimeError):
        return None


def _request_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return request.cookies.get(SESSION_COOKIE)


async def get_current_account(
    request: Request,
    session: AsyncSession = Depends(get_auth_session),
    settings: Settings = Depends(get_settings),
) -> Account:
    decoded = _decode_access_token(_request_token(request) or "", settings)
    if decoded is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired. Please sign in again.")
    account_id, token_version = decoded
    account = await session.get(Account, account_id)
    if account is None or not account.is_active or account.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired. Please sign in again.")
    return account


def require_csrf(request: Request) -> None:
    cookie_value = request.cookies.get(CSRF_COOKIE)
    header_value = request.headers.get(CSRF_HEADER)
    if not cookie_value or not header_value or not hmac.compare_digest(cookie_value, header_value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please refresh and try again.")


def set_session_cookies(response: Response, *, account: Account, settings: Settings) -> None:
    token = create_access_token(account, settings)
    max_age = settings.jwt_access_token_minutes * 60
    common = {
        "max_age": max_age,
        "secure": settings.is_production,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **common)
    response.set_cookie(CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, **common)


def clear_session_cookies(response: Response, *, settings: Settings) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", secure=settings.is_production, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=settings.is_production, samesite="lax")
