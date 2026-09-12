"""Runnable LiveKit AgentServer for the Vyamit realtime voice test lab."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterable, AsyncIterator
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
from app.config.settings import MissingConfigurationError, get_settings
from app.core.logging import configure_logging

_BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent
_LANGUAGE_CONTROL_TOPIC = "vyamit.language.v1"
_MAX_LANGUAGE_CONTROL_BYTES = 256
_VOICE_TAG_PATTERN = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9_-]*)\b[^>]*>")
_INTERNAL_VOICE_TAGS = frozenset({"analysis", "reasoning", "thought", "thinking"})

# Let the agent process see the same local credentials as FastAPI. A
# backend/.env remains the preferred place for backend-specific overrides.
load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_PROJECT_DIRECTORY / ".env.local", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env.local", override=True)

configure_logging()
logger = logging.getLogger("vyamit.agent")


class VyamitAssistant(Agent):
    """The language-aware, voice-first assistant persona."""

    def __init__(self, active_language: str) -> None:
        super().__init__(
            instructions=build_voice_assistant_instructions(LANGUAGE_NAMES[active_language])
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
        logger.exception("language_update_task_failed")


@server.rtc_session(agent_name=get_settings().agent_name)
async def vyamit_voice_agent(ctx: JobContext) -> None:
    """Run one voice session with live, validated language updates."""

    settings = get_settings()
    settings.require_agent_providers()
    ctx.log_context_fields = {"room": ctx.room.name}

    # Waiting is deterministic; the earlier fixed sleep raced token attributes
    # and intermittently discarded the browser's selected language.
    participant = await ctx.wait_for_participant()
    active_language = (
        normalize_language(participant.attributes.get("language"))
        or normalize_language(settings.google_stt_language)
        or "hi-IN"
    )
    language_revision = 0

    logger.info(
        "participant_language_preference participant=%s language=%s",
        participant.identity,
        active_language,
    )

    assistant = VyamitAssistant(active_language)
    session = AgentSession(
        stt=create_stt(settings, primary_language=active_language),
        llm=create_llm(settings),
        tts=create_tts(settings, language=active_language),
        turn_handling=TurnHandlingOptions(turn_detection=inference.TurnDetector()),
        preemptive_generation=True,
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
        language_revision += 1
        logger.info(
            "language_profile_updated participant=%s language=%s source=%s revision=%s",
            participant.identity,
            language,
            source,
            language_revision,
        )
        return language, language_revision, True

    async def announce_language(language: str, source: str, revision: int) -> None:
        """Update the LLM and send the authoritative UI state to its owner only."""

        await assistant.update_instructions(build_voice_assistant_instructions(LANGUAGE_NAMES[language]))
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

    def schedule_language_announcement(language: str, source: str, revision: int) -> None:
        task = asyncio.create_task(announce_language(language, source, revision))
        task.add_done_callback(_log_background_exception)

    @ctx.room.on("data_received")
    def handle_language_control(packet: object) -> None:
        """Accept a compact language command only from this session's browser."""

        if _event_value(packet, "topic", "") != _LANGUAGE_CONTROL_TOPIC:
            return
        sender = _event_value(packet, "participant")
        if sender is None or _event_value(sender, "identity") != participant.identity:
            logger.warning("ignored_language_control reason=unexpected_sender")
            return

        data = _event_value(packet, "data", b"")
        if not isinstance(data, bytes) or len(data) > _MAX_LANGUAGE_CONTROL_BYTES:
            logger.warning("ignored_language_control reason=invalid_payload_size")
            return
        try:
            message = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("ignored_language_control reason=invalid_json")
            return
        if not isinstance(message, dict) or message.get("type") != "set_language":
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

    @session.on("agent_state_changed")
    def log_agent_state(event: object) -> None:
        logger.info("agent_state state=%s", _event_value(event, "state", "unknown"))

    @session.on("user_state_changed")
    def log_user_state(event: object) -> None:
        logger.info("user_state state=%s", _event_value(event, "state", "unknown"))

    @session.on("overlapping_speech")
    def log_interruption(event: object) -> None:
        logger.info("interruption_detected event=%s", type(event).__name__)

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
