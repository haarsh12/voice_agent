"""Small worker client for the memory-only guest session API.

The LiveKit worker runs in a separate process from FastAPI.  This module keeps
that boundary explicit while using the same short-lived session capability that
was already validated before the browser token was issued.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

from app.knowledge.contracts import UserKnowledgeContext


class GuestSessionClientError(RuntimeError):
    """Raised when the worker cannot read or update guest context."""


@dataclass(frozen=True)
class VoiceGuestContext:
    """Capability-protected context supplied to one local voice worker."""

    context: str
    user_context: UserKnowledgeContext | None = None


def _request_json(
    base_url: str,
    *,
    method: str,
    session_id: str,
    session_secret: str,
    suffix: str,
    payload: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Call the local API without logging the guest capability or payload."""

    encoded_id = quote(session_id, safe="")
    url = f"{base_url.rstrip('/')}/api/internal/guest-sessions/{encoded_id}/{suffix.lstrip('/')}"
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Sahayak-Guest-Secret": session_secret,
        },
    )
    try:
        with urlopen(request, timeout=1) as response:  # noqa: S310 - configured local URL
            if response.status == 204:
                return None
            parsed = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise GuestSessionClientError("Guest session context is unavailable.") from error
    if not isinstance(parsed, dict):
        raise GuestSessionClientError("Guest session context response is invalid.")
    return parsed


async def fetch_guest_context(
    base_url: str,
    *,
    session_id: str,
    session_secret: str,
) -> VoiceGuestContext:
    """Fetch the bounded context for current instructions, without blocking audio."""

    response = await asyncio.to_thread(
        _request_json,
        base_url,
        method="GET",
        session_id=session_id,
        session_secret=session_secret,
        suffix="context",
    )
    context = response.get("context") if response else ""
    if not isinstance(context, str):
        raise GuestSessionClientError("Guest session context is invalid.")
    raw_knowledge_context = response.get("knowledge_context") if response else None
    if raw_knowledge_context is None:
        return VoiceGuestContext(context=context)
    if not isinstance(raw_knowledge_context, dict):
        raise GuestSessionClientError("Guest session profile context is invalid.")
    return VoiceGuestContext(
        context=context,
        user_context=UserKnowledgeContext(
            state=_context_value(raw_knowledge_context, "state", 100),
            district=_context_value(raw_knowledge_context, "district", 120),
            village_or_town=_context_value(raw_knowledge_context, "village_or_town", 120),
            user_type=_context_value(raw_knowledge_context, "user_type", 48),
            cooperative_role=_context_value(raw_knowledge_context, "cooperative_role", 120),
        ),
    )


def _context_value(payload: dict[str, Any], key: str, maximum: int) -> str | None:
    """Validate bounded profile data crossing the local HTTP worker boundary."""

    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GuestSessionClientError("Guest session profile context is invalid.")
    normalized = " ".join(value.replace("\x00", " ").split()).strip()
    if len(normalized) > maximum:
        raise GuestSessionClientError("Guest session profile context is invalid.")
    return normalized or None


async def append_voice_turn(
    base_url: str,
    *,
    session_id: str,
    session_secret: str,
    role: str,
    text: str,
) -> None:
    """Forward one final voice turn to the guest session store."""

    await asyncio.to_thread(
        _request_json,
        base_url,
        method="POST",
        session_id=session_id,
        session_secret=session_secret,
        suffix="voice-turns",
        payload={"role": role, "text": text},
    )
