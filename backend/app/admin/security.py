"""Isolated admin authentication for the operational knowledge dashboard."""

from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt

from app.config.settings import MissingConfigurationError, Settings, get_settings

_ALGORITHM = "HS256"
_ADMIN_ROLE = "knowledge_admin"
_ADMIN_SESSION_COOKIE = "sahayak_admin_session"
_ADMIN_CSRF_COOKIE = "sahayak_admin_csrf"
_ADMIN_CSRF_HEADER = "X-Sahayak-Admin-CSRF"
_password_hasher = PasswordHasher()


def verify_admin_credentials(settings: Settings, *, admin_id: str, password: str) -> bool:
    """Verify a configured Argon2id password without exposing which field failed."""

    settings.require_admin_access()
    password_hash = settings.admin_password_hash
    if password_hash is None:
        return False
    try:
        password_valid = _password_hasher.verify(password_hash.get_secret_value(), password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False
    return bool(password_valid and hmac.compare_digest(settings.admin_id, admin_id))


def set_admin_session(response: Response, *, settings: Settings) -> None:
    """Issue an HttpOnly, path-scoped admin cookie plus a CSRF token."""

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.admin_access_token_minutes)
    token = jwt.encode(
        {"sub": "configured-admin", "role": _ADMIN_ROLE, "exp": expires_at},
        settings.require_jwt_secret(),
        algorithm=_ALGORITHM,
    )
    common = {
        "max_age": settings.admin_access_token_minutes * 60,
        "secure": settings.is_production,
        "samesite": "strict",
        "path": "/api/admin",
    }
    response.set_cookie(_ADMIN_SESSION_COOKIE, token, httponly=True, **common)
    response.set_cookie(_ADMIN_CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, **common)


def clear_admin_session(response: Response, *, settings: Settings) -> None:
    """Delete the isolated admin cookies without touching a member session."""

    response.delete_cookie(_ADMIN_SESSION_COOKIE, path="/api/admin", secure=settings.is_production, samesite="strict")
    response.delete_cookie(_ADMIN_CSRF_COOKIE, path="/api/admin", secure=settings.is_production, samesite="strict")


def get_current_admin(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Require an unexpired token issued only by the admin login endpoint."""

    token = request.cookies.get(_ADMIN_SESSION_COOKIE, "")
    try:
        claims = jwt.decode(token, settings.require_jwt_secret(), algorithms=[_ALGORITHM])
    except (JWTError, MissingConfigurationError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin sign-in is required.") from None
    if claims.get("role") != _ADMIN_ROLE or claims.get("sub") != "configured-admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin sign-in is required.")


def require_admin_csrf(request: Request) -> None:
    """Protect state-changing admin routes from cross-site requests."""

    cookie = request.cookies.get(_ADMIN_CSRF_COOKIE, "")
    header = request.headers.get(_ADMIN_CSRF_HEADER, "")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please refresh and try again.")
