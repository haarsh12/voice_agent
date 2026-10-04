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
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

from app.agent.languages import normalize_language
from app.auth.security import get_optional_current_account
from app.auth.session import get_auth_session
from app.config.settings import MissingConfigurationError, Settings, get_settings
from app.knowledge.contracts import Citation, EvidenceStatus, UserKnowledgeContext
from app.knowledge.policy import decide_response
from app.knowledge.retrieval import KnowledgeRetriever, format_evidence_for_model
from app.schemes.repository import SchemeRepository
from app.schemes.voice import discover_for_voice
from app.services.document_text import (
    MAX_UPLOAD_BYTES,
    DocumentExtractionError,
    ExtractedDocument,
    extract_uploaded_document,
)
from app.services.gemini import TextGenerationError, generate_text_reply
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
    """A direct reply with its evidence classification and real citations."""

    message: str
    language: SUPPORTED_LANGUAGES
    document_name: str | None = None
    document_truncated: bool = False
    evidence_status: EvidenceStatus
    sources: list["OfficialSourceReference"] = Field(default_factory=list)


class OfficialSourceReference(BaseModel):
    """A source reference generated from a retrieved current document chunk."""

    name: str
    title: str
    url: str
    document_version: str | None = None
    freshness_status: str


def _source_references(citations: tuple[Citation, ...]) -> list[OfficialSourceReference]:
    """Serialize only citations produced by the retrieval service."""

    return [
        OfficialSourceReference(
            name=citation.source_name,
            title=citation.title,
            url=citation.url,
            document_version=citation.document_version,
            freshness_status=citation.freshness_status.value,
        )
        for citation in citations
    ]


class GuestSessionResponse(BaseModel):
    """A short-lived browser capability for one anonymous conversation."""

    session_id: str
    session_secret: str


class VoiceKnowledgeContext(BaseModel):
    """Location and member-type fields permitted for voice retrieval ranking."""

    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=120)
    village_or_town: str | None = Field(default=None, max_length=120)
    user_type: str | None = Field(default=None, max_length=48)
    cooperative_role: str | None = Field(default=None, max_length=120)


class GuestContextResponse(BaseModel):
    """Bounded, server-only context consumed by the local voice worker."""

    context: str
    knowledge_context: VoiceKnowledgeContext | None = None
    has_reference_documents: bool = False
    # Internal worker-only data; this router is protected by the ephemeral
    # guest capability and never called by the browser.
    account_id: int | None = None


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


def _bind_account_profile_to_guest_session(
    *,
    session_id: str,
    session_secret: str,
    account: object,
) -> None:
    """Copy only useful, server-verified account fields into ephemeral context."""

    guest_sessions.set_member_profile(
        session_id,
        session_secret,
        full_name=getattr(account, "full_name", None),
        phone_number=getattr(account, "phone_number", None),
        state=getattr(account, "state", None),
        district=getattr(account, "district", None),
        village_or_town=getattr(account, "village_or_town", None),
        address=getattr(account, "address", None),
        pincode=getattr(account, "pincode", None),
        caste_category=getattr(account, "caste_category", None),
        user_type=getattr(account, "user_type", None),
        cooperative_role=getattr(account, "cooperative_role", None),
        account_id=getattr(account, "id", None),
    )


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
    profile = snapshot.member_profile
    knowledge_context = (
        VoiceKnowledgeContext(
            state=profile.state,
            district=profile.district,
            village_or_town=profile.village_or_town,
            user_type=profile.user_type,
            cooperative_role=profile.cooperative_role,
        )
        if profile is not None
        else None
    )
    return GuestContextResponse(
        context=snapshot.render_context(max_characters=MAX_AGENT_CONTEXT_CHARACTERS),
        knowledge_context=knowledge_context,
        has_reference_documents=bool(snapshot.documents),
        account_id=snapshot.account_id,
    )


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
    http_request: Request = None,  # type: ignore[assignment]
    session: AsyncSession = Depends(get_auth_session),
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
        normalized_session_id, guest_session_secret, _ = _require_guest_session(
            guest_session_id,
            guest_session_secret,
        )
        guest_session_id = normalized_session_id
        if http_request is not None:
            account = await get_optional_current_account(http_request, session, settings)
            if account is not None:
                _bind_account_profile_to_guest_session(
                    session_id=guest_session_id,
                    session_secret=guest_session_secret,
                    account=account,
                )

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
    session: AsyncSession = Depends(get_auth_session),
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
    account = await get_optional_current_account(request, session, settings)
    if account is not None:
        _bind_account_profile_to_guest_session(
            session_id=guest_session_id,
            session_secret=guest_session_secret,
            account=account,
        )
        # A member may have updated their profile since the session began.
        # Re-read the bounded context so this model call sees the same profile
        # data that the next voice turn will receive.
        snapshot = guest_sessions.snapshot(guest_session_id, guest_session_secret)
    user_context = (
        UserKnowledgeContext(
            state=account.state,
            district=account.district,
            village_or_town=account.village_or_town,
            user_type=account.user_type,
            cooperative_role=account.cooperative_role,
        )
        if account is not None
        else None
    )
    retrieval = await KnowledgeRetriever(session, settings).retrieve(message, user_context=user_context)
    # Text and voice both consult the same canonical catalogue.  Catalogue
    # selections are merged as ordinary verified chunks so the evidence policy
    # still governs benefits, eligibility, dates, and application guidance.
    try:
        scheme_result = await discover_for_voice(
            SchemeRepository(session),
            message=message,
            context=user_context,
        )
    except Exception:
        # A catalogue outage must not make the existing verified retrieval
        # path unavailable.  The policy below still abstains safely if no
        # source evidence was retrieved.
        logger.warning("scheme_catalogue_lookup_unavailable")
        scheme_result = None
    scheme_instruction = ""
    if scheme_result is not None and scheme_result.page.items:
        try:
            catalogue_evidence = await SchemeRepository(session).evidence_for_schemes(
                [item.id for item in scheme_result.page.items]
            )
            combined = {item.chunk_id: item for item in (*catalogue_evidence, *retrieval.evidence)}
            retrieval = type(retrieval)(evidence=tuple(combined.values()), unavailable_reason=retrieval.unavailable_reason)
            names = "\n".join(f"- {item.official_name} ({item.scheme_type}; {item.category})" for item in scheme_result.page.items)
            more = max(scheme_result.page.total - len(scheme_result.page.items), 0)
            scheme_instruction = (
                "\nVERIFIED SCHEME DIRECTORY RESULTS\n"
                f"{names}\nMore verified records: {more}. Do not promise eligibility or invent absent details. "
                "Do not send the user to another website; explain the available in-app guidance.\n"
            )
        except Exception:
            logger.warning("scheme_catalogue_evidence_unavailable")
    decision = decide_response(
        message=message,
        language=language,
        retrieval=retrieval,
        # Attached and already-session-scoped documents can be explained, but
        # the model must not represent them as verified current policy.
        has_reference_document=bool(document or snapshot.documents),
    )

    if decision.requires_abstention:
        reply = decision.abstention_message or "That detail is not yet available in Sahayak AI's knowledge base."
    else:
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
                    verified_evidence=format_evidence_for_model(decision.retrieval.evidence) + scheme_instruction,
                    evidence_status=decision.evidence_status.value,
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
        evidence_status=decision.evidence_status,
        sources=_source_references(decision.retrieval.citations),
    )
