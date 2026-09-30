"""Runnable LiveKit AgentServer for the Sahayak AI voice assistant."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import deque
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
    llm,
    room_io,
)
from livekit.plugins import ai_coustics

from app.agent.languages import LANGUAGE_NAMES, normalize_language
from app.agent.prompts import build_voice_assistant_instructions
from app.agent.providers import (
    create_llm,
    create_stt,
    create_tts,
    update_stt_language,
    update_tts_language,
)
from app.auth.session import ensure_development_auth_schema, get_engine
from app.config.settings import MissingConfigurationError, get_settings
from app.core.logging import configure_logging
from app.knowledge.contracts import Citation, EvidenceStatus, UserKnowledgeContext
from app.knowledge.voice import VoiceKnowledgeService, VoiceKnowledgeTurn
from app.services.guest_session_client import (
    GuestSessionClientError,
    append_voice_turn,
    fetch_guest_context,
)

_BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent
_LANGUAGE_CONTROL_TOPIC = "sahayak.language.v1"
_CONTEXT_CONTROL_TOPIC = "sahayak.context.v1"
_CITATION_CONTROL_TOPIC = "sahayak.citations.v1"
_MAX_LANGUAGE_CONTROL_BYTES = 256
_VOICE_TAG_PATTERN = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9_-]*)\b[^>]*>")
_INTERNAL_VOICE_TAGS = frozenset({"analysis", "reasoning", "thought", "thinking"})
_INTERNAL_VOICE_BLOCK_PATTERN = re.compile(
    r"<\s*(?:analysis|reasoning|thought|thinking)\b[^>]*>[\s\S]*?"
    r"(?:<\s*/\s*(?:analysis|reasoning|thought|thinking)\s*>|$)",
    re.IGNORECASE,
)
VOICE_TURN_HANDLING_OPTIONS: TurnHandlingOptions = {
    "turn_detection": inference.TurnDetector(),
    "interruption": {
        "enabled": True,
        "min_duration": 0.35,
        "min_words": 1,
        # A member's spoken follow-up must replace an unfinished answer.
        "resume_false_interruption": False,
        "false_interruption_timeout": None,
        "backchannel_boundary": None,
    },
    # Waiting for a completed utterance prevents a draft answer from surviving
    # a changed or interrupted user request.
    "preemptive_generation": {"enabled": False},
}

# Let the agent process see the same local credentials as FastAPI. A
# backend/.env remains the preferred place for backend-specific overrides.
load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_PROJECT_DIRECTORY / ".env.local", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env.local", override=True)

configure_logging()
logger = logging.getLogger("sahayak.agent")


@dataclass(frozen=True)
class VoiceCitationUpdate:
    """Citation data published visually after the matching voice reply."""

    evidence_status: EvidenceStatus
    citations: tuple[Citation, ...]


class SahayakAssistant(Agent):
    """The language-aware, voice-first assistant persona."""

    def __init__(
        self,
        active_language: str,
        knowledge_service: VoiceKnowledgeService,
        guest_context: str = "",
        user_context: UserKnowledgeContext | None = None,
        has_reference_documents: bool = False,
    ) -> None:
        super().__init__(
            instructions=build_voice_assistant_instructions(
                LANGUAGE_NAMES[active_language], guest_context
            )
        )
        self._active_language = active_language
        self._knowledge_service = knowledge_service
        self._user_context = user_context
        self._has_reference_documents = has_reference_documents
        self._citation_updates: deque[VoiceCitationUpdate] = deque(maxlen=8)

    def set_active_language(self, language: str) -> None:
        """Keep retrieval abstentions in the same language as STT/TTS."""

        self._active_language = language

    def consume_citation_update(self) -> VoiceCitationUpdate | None:
        """Pair the oldest grounded user turn with its completed assistant turn."""

        return self._citation_updates.popleft() if self._citation_updates else None

    def discard_pending_citation_updates(self) -> None:
        """Discard metadata for a reply that the member has interrupted."""

        self._citation_updates.clear()

    def set_user_context(self, user_context: UserKnowledgeContext | None) -> None:
        """Keep location-aware retrieval aligned with the current profile snapshot."""

        self._user_context = user_context

    def set_has_reference_documents(self, has_reference_documents: bool) -> None:
        """Allow explanation of a session document without treating it as policy."""

        self._has_reference_documents = has_reference_documents

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        """Ground the next voice response before the LiveKit LLM starts."""

        message = _conversation_item_text(new_message)
        if not message:
            return
        knowledge_turn: VoiceKnowledgeTurn = await self._knowledge_service.prepare_turn(
            message=message,
            language=self._active_language,
            user_context=self._user_context,
            has_reference_document=self._has_reference_documents,
        )
        # This context is scoped to this one reply. The LLM receives evidence
        # text but never source URLs, and TTS receives only the final answer.
        turn_ctx.add_message(role="developer", content=knowledge_turn.instructions)
        self._citation_updates.append(
            VoiceCitationUpdate(
                evidence_status=knowledge_turn.evidence_status,
                citations=knowledge_turn.citations,
            )
        )


server = AgentServer()


def _event_value(event: object, name: str, default: Any = None) -> Any:
    """Read event values defensively so observability never breaks a call."""

    return getattr(event, name, default)


async def strip_internal_voice_markup(chunks: AsyncIterable[str]) -> AsyncIterator[str]:
    """Prevent accidental model reasoning/XML from reaching speech output.

    The model is instructed to use plain text, but this streaming guard removes
    wrapper tags and discards the contents of internal reasoning tags even when
    a tag is split across provider chunks.
    """

    buffer = ""
    suppressed_tag: str | None = None

    async for chunk in chunks:
        buffer += chunk
        while True:
            match = _VOICE_TAG_PATTERN.search(buffer)
            if match is None:
                # Hold a possible partial tag until the next streaming chunk.
                partial_tag_start = buffer.rfind("<")
                if partial_tag_start >= 0 and re.fullmatch(
                    r"</?[A-Za-z][A-Za-z0-9_-]*", buffer[partial_tag_start:]
                ):
                    visible, buffer = buffer[:partial_tag_start], buffer[partial_tag_start:]
                else:
                    visible, buffer = buffer, ""
                if visible and suppressed_tag is None:
                    yield visible
                break

            visible = buffer[: match.start()]
            if visible and suppressed_tag is None:
                yield visible

            is_closing_tag = bool(match.group(1))
            tag_name = match.group(2).lower()
            if is_closing_tag and suppressed_tag == tag_name:
                suppressed_tag = None
            elif not is_closing_tag and tag_name in _INTERNAL_VOICE_TAGS:
                suppressed_tag = tag_name
            buffer = buffer[match.end() :]

    if suppressed_tag is None and buffer:
        # Do not speak an unfinished tag at the end of a model response.
        remaining = re.sub(r"<[^>]*$", "", buffer)
        if remaining:
            yield remaining


def _log_background_exception(task: asyncio.Task[object]) -> None:
    """Make failed data-channel work visible without crashing the call."""

    if task.cancelled():
        return
    try:
        task.result()
    except Exception:
        logger.exception("background_session_task_failed")


def _clean_voice_context_text(value: object) -> str:
    """Keep accidental private reasoning out of the shared guest context."""

    if not isinstance(value, str):
        return ""
    return (
        _INTERNAL_VOICE_BLOCK_PATTERN.sub("", value)
        .replace("<thought>", "")
        .replace("</thought>", "")
        .replace("\x00", "")
        .strip()
    )[:2_000]


def _conversation_item_text(item: object) -> str:
    """Extract a final LiveKit chat item's visible text across SDK shapes."""

    direct_text = _event_value(item, "text_content")
    if isinstance(direct_text, str):
        return _clean_voice_context_text(direct_text)

    content = _event_value(item, "content")
    if isinstance(content, str):
        return _clean_voice_context_text(content)
    if isinstance(content, list):
        fragments: list[str] = []
        for fragment in content:
            if isinstance(fragment, str):
                fragments.append(fragment)
            else:
                text = _event_value(fragment, "text")
                if isinstance(text, str):
                    fragments.append(text)
        return _clean_voice_context_text("".join(fragments))
    return ""


@server.rtc_session(agent_name=get_settings().agent_name)
async def sahayak_voice_agent(ctx: JobContext) -> None:
    """Run one voice session with live, validated language updates."""

    settings = get_settings()
    settings.require_agent_providers()
    engine = get_engine()
    if (
        engine is not None
        and not settings.is_production
        and settings.async_database_url
        and settings.async_database_url.startswith("sqlite")
    ):
        await ensure_development_auth_schema(engine)
    ctx.log_context_fields = {"room": ctx.room.name}

    # Waiting is deterministic; the earlier fixed sleep raced token attributes
    # and intermittently discarded the browser's selected language.
    participant = await ctx.wait_for_participant()
    active_language = (
        normalize_language(participant.attributes.get("language"))
        or normalize_language(settings.google_stt_language)
        or "hi-IN"
    )
    guest_session_id = participant.attributes.get("guest_session_id")
    guest_session_secret = participant.attributes.get("guest_session_secret")
    if bool(guest_session_id) != bool(guest_session_secret):
        logger.warning("guest_context_ignored reason=incomplete_participant_attributes")
        guest_session_id = None
        guest_session_secret = None

    guest_context = ""
    user_context: UserKnowledgeContext | None = None
    has_reference_documents = False
    if guest_session_id and guest_session_secret:
        try:
            voice_context = await fetch_guest_context(
                settings.guest_session_api_url,
                session_id=guest_session_id,
                session_secret=guest_session_secret,
            )
            guest_context = voice_context.context
            user_context = voice_context.user_context
            has_reference_documents = voice_context.has_reference_documents
        except GuestSessionClientError:
            # Context enhances the call but an unavailable local API should
            # never prevent the voice agent from starting a conversation.
            logger.warning("guest_context_unavailable phase=initial_load")
    language_revision = 0

    logger.info(
        "participant_language_preference participant=%s language=%s",
        participant.identity,
        active_language,
    )

    assistant = SahayakAssistant(
        active_language,
        VoiceKnowledgeService(settings),
        guest_context,
        user_context,
        has_reference_documents,
    )
    session = AgentSession(
        stt=create_stt(settings, primary_language=active_language),
        llm=create_llm(settings),
        tts=create_tts(settings, language=active_language),
        turn_handling=VOICE_TURN_HANDLING_OPTIONS,
        use_tts_aligned_transcript=True,
        tts_text_transforms=["filter_markdown", "filter_emoji", strip_internal_voice_markup],
    )

    def apply_language_profile(candidate: object, *, source: str) -> tuple[str, int, bool] | None:
        """Synchronously update STT/TTS before a reply can be synthesized."""

        nonlocal active_language, language_revision
        language = normalize_language(candidate)
        if language is None:
            return None
        if language == active_language:
            return language, language_revision, False

        if session.stt is not None:
            update_stt_language(session.stt, language=language)
        if session.tts is not None:
            update_tts_language(session.tts, language=language)

        active_language = language
        assistant.set_active_language(language)
        language_revision += 1
        logger.info(
            "language_profile_updated participant=%s language=%s source=%s revision=%s",
            participant.identity,
            language,
            source,
            language_revision,
        )
        return language, language_revision, True

    async def refresh_guest_context() -> None:
        """Pull latest text/document history before the next voice reply."""

        nonlocal guest_context, user_context, has_reference_documents
        if not guest_session_id or not guest_session_secret:
            return
        try:
            voice_context = await fetch_guest_context(
                settings.guest_session_api_url,
                session_id=guest_session_id,
                session_secret=guest_session_secret,
            )
            guest_context = voice_context.context
            user_context = voice_context.user_context
            has_reference_documents = voice_context.has_reference_documents
        except GuestSessionClientError:
            logger.warning("guest_context_unavailable phase=refresh")
            return
        assistant.set_user_context(user_context)
        assistant.set_has_reference_documents(has_reference_documents)
        await assistant.update_instructions(
            build_voice_assistant_instructions(LANGUAGE_NAMES[active_language], guest_context)
        )

    async def announce_language(language: str, source: str, revision: int) -> None:
        """Update the LLM and send the authoritative UI state to its owner only."""

        await assistant.update_instructions(
            build_voice_assistant_instructions(LANGUAGE_NAMES[language], guest_context)
        )
        if revision != language_revision:
            return

        payload = json.dumps(
            {
                "type": "language_change",
                "language": language,
                "source": source,
                "revision": revision,
            },
            separators=(",", ":"),
        )
        await ctx.room.local_participant.publish_data(
            payload,
            reliable=True,
            destination_identities=[participant.identity],
            topic=_LANGUAGE_CONTROL_TOPIC,
        )

    async def publish_voice_citations(update: VoiceCitationUpdate, assistant_text: str) -> None:
        """Send references through LiveKit data, never through the speech stream."""

        payload = json.dumps(
            {
                "type": "voice_evidence",
                "evidence_status": update.evidence_status.value,
                # The UI matches this final text rather than guessing based on
                # arrival order, which keeps citations off an interrupted turn.
                "reply_text": assistant_text,
                "sources": [
                    {
                        "name": citation.source_name,
                        "title": citation.title,
                        "url": citation.url,
                        "document_version": citation.document_version,
                        "freshness_status": citation.freshness_status.value,
                    }
                    for citation in update.citations
                ],
            },
            separators=(",", ":"),
        )
        await ctx.room.local_participant.publish_data(
            payload,
            reliable=True,
            destination_identities=[participant.identity],
            topic=_CITATION_CONTROL_TOPIC,
        )

    def schedule_language_announcement(language: str, source: str, revision: int) -> None:
        task = asyncio.create_task(announce_language(language, source, revision))
        task.add_done_callback(_log_background_exception)

    @ctx.room.on("data_received")
    def handle_language_control(packet: object) -> None:
        """Accept a compact language command only from this session's browser."""

        topic = _event_value(packet, "topic", "")
        if topic not in {_LANGUAGE_CONTROL_TOPIC, _CONTEXT_CONTROL_TOPIC}:
            return
        sender = _event_value(packet, "participant")
        if sender is None or _event_value(sender, "identity") != participant.identity:
            logger.warning("ignored_session_control reason=unexpected_sender")
            return

        data = _event_value(packet, "data", b"")
        if not isinstance(data, bytes) or len(data) > _MAX_LANGUAGE_CONTROL_BYTES:
            logger.warning("ignored_session_control reason=invalid_payload_size")
            return
        try:
            message = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("ignored_session_control reason=invalid_json")
            return
        if not isinstance(message, dict):
            logger.warning("ignored_session_control reason=unsupported_message")
            return

        if topic == _CONTEXT_CONTROL_TOPIC:
            if message.get("type") != "refresh_context":
                logger.warning("ignored_context_control reason=unsupported_message")
                return
            task = asyncio.create_task(refresh_guest_context())
            task.add_done_callback(_log_background_exception)
            return

        if message.get("type") != "set_language":
            logger.warning("ignored_language_control reason=unsupported_message")
            return

        result = apply_language_profile(message.get("language"), source="manual")
        if result is None:
            logger.warning("ignored_language_control reason=unsupported_language")
            return
        language, revision, _ = result
        schedule_language_announcement(language, "manual", revision)

    @session.on("user_input_transcribed")
    def log_user_transcript(event: object) -> None:
        transcript = _event_value(event, "transcript", "")
        language = _event_value(event, "language")
        is_final = bool(_event_value(event, "is_final", False))
        logger.info(
            "stt_transcript final=%s language=%s chars=%s",
            is_final,
            language,
            len(transcript),
        )

        # Language selection is deliberately manual. The transcript locale is
        # logged for diagnostics only; it must not replace the user's selected
        # STT/TTS profile in the middle of a call.

    @session.on("conversation_item_added")
    def retain_final_voice_turn(event: object) -> None:
        """Merge finalized LiveKit speech into this guest session's memory."""

        item = _event_value(event, "item", event)
        role = _event_value(item, "role")
        if role not in {"user", "assistant"}:
            return
        text = _conversation_item_text(item)
        if not text:
            return

        if role == "assistant":
            if bool(_event_value(item, "interrupted", False)):
                assistant.discard_pending_citation_updates()
                # A partial reply must neither gain sources nor pollute the
                # next turn's memory; the member's new utterance is primary.
                return
            citation_update = assistant.consume_citation_update()
            if citation_update is not None:
                task = asyncio.create_task(publish_voice_citations(citation_update, text))
                task.add_done_callback(_log_background_exception)

        if not guest_session_id or not guest_session_secret:
            return

        task = asyncio.create_task(
            append_voice_turn(
                settings.guest_session_api_url,
                session_id=guest_session_id,
                session_secret=guest_session_secret,
                role=role,
                text=text,
            )
        )
        task.add_done_callback(_log_background_exception)

    @session.on("agent_state_changed")
    def log_agent_state(event: object) -> None:
        logger.info("agent_state state=%s", _event_value(event, "state", "unknown"))

    @session.on("user_state_changed")
    def log_user_state(event: object) -> None:
        logger.info("user_state state=%s", _event_value(event, "state", "unknown"))

    @session.on("overlapping_speech")
    def log_interruption(event: object) -> None:
        is_interruption = bool(_event_value(event, "is_interruption", False))
        if is_interruption:
            assistant.discard_pending_citation_updates()
        logger.info("interruption_detected confirmed=%s", is_interruption)

    @session.on("agent_false_interruption")
    def log_false_interruption(event: object) -> None:
        logger.info("false_interruption event=%s", type(event).__name__)

    @session.on("session_usage_updated")
    def log_usage(event: object) -> None:
        usage = _event_value(event, "usage")
        for model_usage in _event_value(usage, "model_usage", []):
            logger.info(
                "model_usage provider=%s model=%s data=%s",
                _event_value(model_usage, "provider", "unknown"),
                _event_value(model_usage, "model", "unknown"),
                model_usage,
            )

    room_options = room_io.RoomOptions()
    if settings.enable_enhanced_noise_cancellation:
        room_options = room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                )
            )
        )

    try:
        await session.start(agent=assistant, room=ctx.room, room_options=room_options)
        logger.info("session_started room=%s", ctx.room.name)
    except Exception:
        logger.exception("session_start_failed room=%s", ctx.room.name)
        raise


if __name__ == "__main__":
    try:
        get_settings().require_agent_providers()
        cli.run_app(server)
    except MissingConfigurationError as error:
        logger.error("configuration_error %s", error)
        raise SystemExit(2) from error
