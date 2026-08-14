"""Short-lived, least-privilege browser tokens for one configured voice agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from livekit import api

from app.config.settings import Settings


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """The exact current LiveKit TokenSource endpoint response shape."""

    server_url: str
    participant_token: str


def issue_browser_token(
    settings: Settings,
    *,
    room_name: str,
    participant_name: str,
    participant_identity: str | None = None,
) -> IssuedToken:
    """Create a fifteen-minute token and dispatch only this backend's agent.

    Agent dispatch is authored by the server instead of trusting arbitrary room
    configuration supplied by a browser request.
    """

    settings.require_token_issuer()
    identity = participant_identity or f"web-{uuid4().hex}"
    token = (
        api.AccessToken(
            settings.livekit_api_key.get_secret_value(),
            settings.livekit_api_secret.get_secret_value(),
        )
        .with_identity(identity)
        .with_name(participant_name)
        .with_ttl(timedelta(minutes=15))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=settings.agent_name)]
            )
        )
    )
    return IssuedToken(server_url=settings.livekit_url, participant_token=token.to_jwt())
