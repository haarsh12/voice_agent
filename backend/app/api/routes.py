"""Small server-only API: health information and short-lived LiveKit tokens."""

from __future__ import annotations

import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config.settings import MissingConfigurationError, Settings, get_settings
from app.services.token_issuer import IssuedToken, issue_browser_token

router = APIRouter(prefix="/api")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,96}$")


class TokenRequest(BaseModel):
    """Optional room metadata; generated values keep this test lab multi-user safe."""

    room_name: str | None = Field(default=None, max_length=96)
    participant_name: str | None = Field(default=None, max_length=64)


class ConnectionDetails(BaseModel):
    """Current `TokenSource.endpoint` response, intentionally limited to two fields."""

    server_url: str
    participant_token: str


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str | bool]:
    """A credential-free readiness response for the frontend and local checks."""

    return {
        "status": "ok",
        "agent_name": settings.agent_name,
        "configured": settings.agent_providers_configured,
    }


@router.post("/token", response_model=ConnectionDetails)
async def create_token(
    request: TokenRequest | None = None,
    settings: Settings = Depends(get_settings),
) -> ConnectionDetails:
    """Issue a fifteen-minute browser token without ever returning API secrets."""

    try:
        settings.require_token_issuer()
    except MissingConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LiveKit token service is not configured.",
        ) from error

    request = request or TokenRequest()
    room_name = request.room_name or f"vyamit-{uuid4().hex[:12]}"
    participant_name = request.participant_name or "Guest"
    if not _SAFE_NAME.fullmatch(room_name):
        raise HTTPException(status_code=422, detail="room_name contains unsupported characters.")

    issued: IssuedToken = issue_browser_token(
        settings,
        room_name=room_name,
        participant_name=participant_name,
    )
    return ConnectionDetails(
        server_url=issued.server_url,
        participant_token=issued.participant_token,
    )
