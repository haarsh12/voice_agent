"""Small server-only API: health information and short-lived LiveKit tokens."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections import defaultdict, deque
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from starlette.datastructures import UploadFile

from app.agent.languages import normalize_language
from app.config.settings import MissingConfigurationError, Settings, get_settings
from app.services.document_text import (
    MAX_UPLOAD_BYTES,
    DocumentExtractionError,
    ExtractedDocument,
    extract_uploaded_document,
)
from app.services.gemini import TextGenerationError, generate_text_reply
from app.services.official_sources import OfficialSource, select_official_sources
from app.services.guest_sessions import (
    MAX_AGENT_CONTEXT_CHARACTERS,
    GuestSessionError,
    guest_sessions,
)
from app.services.token_issuer import IssuedToken, issue_browser_token

router = APIRouter(prefix="/api")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,96}$")
_MAX_CHAT_MESSAGE_CHARACTERS = 4_000
_MAX_CHAT_REQUEST_BYTES = MAX_UPLOAD_BYTES + 128 * 1024
_CHAT_REQUESTS_PER_MINUTE = 12
_CHAT_RATE_LIMIT_WINDOW_SECONDS = 60.0
_GUEST_SECRET_HEADER = "X-Sahayak-Guest-Secret"
_chat_rate_limit: dict[str, deque[float]] = defaultdict(deque)
logger = logging.getLogger("sahayak.api")

# Supported languages for STT/TTS (validated list from Google Cloud)
SUPPORTED_LANGUAGES = Literal[
    "hi-IN",  # Hindi
    "mr-IN",  # Marathi
    "en-IN",  # English (India)
    "ta-IN",  # Tamil
    "te-IN",  # Telugu
    "kn-IN",  # Kannada
    "ml-IN",  # Malayalam
    "gu-IN",  # Gujarati
    "bn-IN",  # Bengali
    "pa-IN",  # Punjabi
]


class TokenRequest(BaseModel):
    """LiveKit token bootstrap fields accepted from the browser.

    ``participant_attributes`` is the standard shape emitted by
    ``TokenSource.endpoint``. Only its language value is trusted and copied to
    the generated token; callers cannot inject arbitrary participant metadata.
    """

    room_name: str | None = Field(default=None, max_length=96)
    participant_name: str | None = Field(default=None, max_length=64)
    language: SUPPORTED_LANGUAGES | None = Field(
        default=None,
        description="Preferred language for STT/TTS (e.g., 'hi-IN', 'mr-IN', 'en-IN')"
    )
    participant_attributes: dict[str, str] = Field(default_factory=dict, max_length=4)


class ConnectionDetails(BaseModel):
    """Current `TokenSource.endpoint` response, intentionally limited to two fields."""

    server_url: str
    participant_token: str


class ChatResponse(BaseModel):
    """A direct text reply with only reviewed official source metadata."""

    message: str
    language: SUPPORTED_LANGUAGES
    document_name: str | None = None
    document_truncated: bool = False
    sources: list["OfficialSourceReference"] = Field(default_factory=list)


class OfficialSourceReference(BaseModel):
    """A reviewed official link rendered below a text-chat response."""

    name: str
    url: str


def _source_references(message: str) -> list[OfficialSourceReference]:
    """Map user intent to allowlisted official links, never model-provided URLs."""

    sources: tuple[OfficialSource, ...] = select_official_sources(message)
    return [OfficialSourceReference(name=source.name, url=source.url) for source in sources]


class GuestSessionResponse(BaseModel):
    """A short-lived browser capability for one anonymous conversation."""

    session_id: str
    session_secret: str


class GuestContextResponse(BaseModel):
    """Bounded, server-only context consumed by the local voice worker."""

    context: str


class VoiceTurnRequest(BaseModel):
    """A finalized LiveKit voice turn forwarded by the local worker."""

    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=2_000)


def _guest_session_id(value: object) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail="guest_session_id must be text.")
    try:
        return str(UUID(value))
    except ValueError as error:
        raise HTTPException(status_code=422, detail="guest_session_id is invalid.") from error


def _require_guest_session(session_id: object, secret: object):
    if not isinstance(secret, str) or not secret:
        raise HTTPException(status_code=422, detail="guest_session_secret is required.")
    normalized_id = _guest_session_id(session_id)
    try:
        return normalized_id, secret, guest_sessions.snapshot(normalized_id, secret)
    except GuestSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This guest session has ended. Start a new session to continue.",
        ) from error


def _enforce_chat_rate_limit(client_host: str) -> None:
    """Apply a small in-process request limit to the unauthenticated chat API."""

    now = time.monotonic()
    requests = _chat_rate_limit[client_host]
    while requests and now - requests[0] >= _CHAT_RATE_LIMIT_WINDOW_SECONDS:
        requests.popleft()
    if len(requests) >= _CHAT_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many chat requests. Please wait a minute and try again.",
        )
    requests.append(now)


def _multipart_string(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=422, detail=f"{field} must be text.")
    return value


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str | bool]:
    """A credential-free readiness response for the frontend and local checks."""

    return {
        "status": "ok",
        "agent_name": settings.agent_name,
        "configured": settings.agent_providers_configured,
        "default_language": normalize_language(settings.google_stt_language) or "hi-IN",
    }


@router.post("/guest-sessions", response_model=GuestSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_guest_session() -> GuestSessionResponse:
    """Create an in-memory context capability for one anonymous browser session."""

    session_id, session_secret = guest_sessions.create()
    return GuestSessionResponse(session_id=session_id, session_secret=session_secret)


@router.delete("/guest-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guest_session(session_id: str, request: Request) -> None:
    """Forget an authenticated guest session and all its in-memory references."""

    normalized_id = _guest_session_id(session_id)
    secret = request.headers.get(_GUEST_SECRET_HEADER, "")
    try:
        guest_sessions.delete(normalized_id, secret)
    except GuestSessionError as error:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Guest session has ended.") from error


@router.get("/internal/guest-sessions/{session_id}/context", response_model=GuestContextResponse)
async def get_voice_guest_context(session_id: str, request: Request) -> GuestContextResponse:
    """Return bounded context only to a worker with the guest-session capability."""

    normalized_id = _guest_session_id(session_id)
    secret = request.headers.get(_GUEST_SECRET_HEADER, "")
    try:
        snapshot = guest_sessions.snapshot(normalized_id, secret)
    except GuestSessionError as error:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Guest session has ended.") from error
    return GuestContextResponse(context=snapshot.render_context(max_characters=MAX_AGENT_CONTEXT_CHARACTERS))


@router.post("/internal/guest-sessions/{session_id}/voice-turns", status_code=status.HTTP_204_NO_CONTENT)
async def add_voice_guest_turn(
    session_id: str,
    request: Request,
    turn: VoiceTurnRequest,
) -> None:
    """Append a final voice turn without exposing guest data to other callers."""

    normalized_id = _guest_session_id(session_id)
    secret = request.headers.get(_GUEST_SECRET_HEADER, "")
    try:
        guest_sessions.append_turn(
            normalized_id,
            secret,
            role=turn.role,
            text=turn.text,
            source="voice",
        )
    except GuestSessionError as error:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Guest session has ended.") from error


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
    room_name = request.room_name or f"sahayak-{uuid4().hex[:12]}"
    participant_name = request.participant_name or "Guest"
    requested_language = request.language or request.participant_attributes.get("language")
    language = normalize_language(requested_language)
    guest_session_id = request.participant_attributes.get("guest_session_id")
    guest_session_secret = request.participant_attributes.get("guest_session_secret")

    if requested_language is not None and language is None:
        raise HTTPException(status_code=422, detail="language is not supported.")
    if bool(guest_session_id) != bool(guest_session_secret):
        raise HTTPException(status_code=422, detail="guest session attributes are incomplete.")
    if guest_session_id and guest_session_secret:
        _, _, _ = _require_guest_session(guest_session_id, guest_session_secret)

    if not _SAFE_NAME.fullmatch(room_name):
        raise HTTPException(status_code=422, detail="room_name contains unsupported characters.")

    issued: IssuedToken = issue_browser_token(
        settings,
        room_name=room_name,
        participant_name=participant_name,
        language=language,
        guest_session_id=guest_session_id,
        guest_session_secret=guest_session_secret,
    )
    return ConnectionDetails(
        server_url=issued.server_url,
        participant_token=issued.participant_token,
    )


@router.post("/chat", response_model=ChatResponse)
async def create_text_chat_reply(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    """Accept a text message and optional document, then return a text-only reply."""

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > _MAX_CHAT_REQUEST_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="The chat request is too large. Documents must be 5 MB or smaller.",
                )
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from error

    _enforce_chat_rate_limit(request.client.host if request.client else "unknown")

    try:
        # Four small text fields (message, language, session id, session
        # capability) plus one optional upload are expected. Leave a modest
        # margin for multipart encoders while still rejecting field floods.
        async with request.form(max_files=1, max_fields=8, max_part_size=MAX_UPLOAD_BYTES) as form:
            message = _multipart_string(form.get("message", ""), field="message").strip()
            language_value = _multipart_string(form.get("language", "hi-IN"), field="language")
            guest_session_id, guest_session_secret, snapshot = _require_guest_session(
                form.get("guest_session_id"),
                form.get("guest_session_secret"),
            )
            upload = form.get("document")
            if upload is not None and not isinstance(upload, UploadFile):
                raise HTTPException(status_code=422, detail="document must be a file.")

            if len(message) > _MAX_CHAT_MESSAGE_CHARACTERS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Messages are limited to {_MAX_CHAT_MESSAGE_CHARACTERS} characters.",
                )
            language = normalize_language(language_value)
            if language is None:
                raise HTTPException(status_code=422, detail="language is not supported.")
            if not message and upload is None:
                raise HTTPException(status_code=422, detail="Enter a message or attach a document.")

            attachment = None
            if upload is not None:
                try:
                    attachment = await extract_uploaded_document(upload)
                except DocumentExtractionError as error:
                    raise HTTPException(status_code=422, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.info("chat_upload_rejected reason=%s", type(error).__name__)
        raise HTTPException(status_code=422, detail="The chat form could not be processed.") from error

    if not message:
        message = "Please summarize the attached file and highlight the most useful information."

    document = attachment if isinstance(attachment, ExtractedDocument) else None
    image = attachment if attachment is not None and not isinstance(attachment, ExtractedDocument) else None

    try:
        reply = await asyncio.wait_for(
            asyncio.to_thread(
                generate_text_reply,
                settings,
                message=message,
                language=language,
                document_text=document.text if document else None,
                document_truncated=document.truncated if document else False,
                image_data=image.data if image else None,
                image_mime_type=image.mime_type if image else None,
                guest_context=snapshot.render_context(max_characters=MAX_AGENT_CONTEXT_CHARACTERS),
            ),
            timeout=45,
        )
    except asyncio.TimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The assistant took too long to reply. Please try again.",
        ) from error
    except (MissingConfigurationError, TextGenerationError) as error:
        logger.warning("text_chat_unavailable reason=%s", type(error).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Text chat is not available right now. Please try again shortly.",
        ) from error
    except Exception:
        logger.exception("text_chat_generation_failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant could not generate a reply. Please try again.",
        ) from None

    if document is not None:
        try:
            guest_sessions.add_document(guest_session_id, guest_session_secret, document)
        except GuestSessionError as error:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Guest session has ended.") from error
    turn_text = message
    if attachment is not None:
        turn_text = f"{turn_text}\n[Attached file: {attachment.filename}]"
    try:
        guest_sessions.append_turn(
            guest_session_id,
            guest_session_secret,
            role="user",
            text=turn_text,
            source="text",
        )
        guest_sessions.append_turn(
            guest_session_id,
            guest_session_secret,
            role="assistant",
            text=reply,
            source="text",
        )
    except GuestSessionError as error:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Guest session has ended.") from error

    return ChatResponse(
        message=reply,
        language=language,
        document_name=attachment.filename if attachment else None,
        document_truncated=document.truncated if document else False,
        sources=_source_references(message),
    )
