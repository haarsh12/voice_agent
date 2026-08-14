"""Runnable LiveKit AgentServer for the Vyamit realtime voice test lab."""

from __future__ import annotations

import logging
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

from app.agent.prompts import VOICE_ASSISTANT_INSTRUCTIONS
from app.agent.providers import create_llm, create_stt, create_tts
from app.config.settings import MissingConfigurationError, get_settings
from app.core.logging import configure_logging

_BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent

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

    def __init__(self) -> None:
        super().__init__(instructions=VOICE_ASSISTANT_INSTRUCTIONS)


server = AgentServer()


def _event_value(event: object, name: str, default: Any = None) -> Any:
    """Read event values defensively so metrics logging never breaks a call."""

    return getattr(event, name, default)


@server.rtc_session(agent_name=get_settings().agent_name)
async def vyamit_voice_agent(ctx: JobContext) -> None:
    """Start one streaming STT → Mistral → TTS session for a LiveKit room."""

    settings = get_settings()
    settings.require_agent_providers()
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=create_stt(settings),
        llm=create_llm(settings),
        tts=create_tts(settings),
        # LiveKit's turn detector adds semantic endpointing while bundled VAD
        # powers quick speech interruption detection.
        turn_handling=TurnHandlingOptions(turn_detection=inference.TurnDetector()),
        preemptive_generation=True,
        use_tts_aligned_transcript=True,
    )

    @session.on("user_input_transcribed")
    def log_user_transcript(event: object) -> None:
        transcript = _event_value(event, "transcript", "")
        is_final = bool(_event_value(event, "is_final", False))
        language = _event_value(event, "language")
        logger.info(
            "stt_transcript final=%s language=%s chars=%s",
            is_final,
            language,
            len(transcript),
        )
        # Cartesia applies changed options to the next utterance. Deepgram's
        # final transcript language therefore selects Hindi/Marathi/English
        # voice synthesis without rebuilding the session.
        if is_final and language in {"en", "hi", "mr"}:
            session.tts.update_options(language=language)

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

    # AgentSession.start requires a RoomOptions instance when the argument is
    # supplied; passing None causes the worker to crash before joining a room.
    room_options = room_io.RoomOptions()
    if settings.enable_enhanced_noise_cancellation:
        room_options = room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                )
            )
        )

    await session.start(
        agent=VyamitAssistant(),
        room=ctx.room,
        room_options=room_options,
    )
    await ctx.connect()
    logger.info("session_started room=%s", ctx.room.name)


if __name__ == "__main__":
    try:
        # Fail before accepting any LiveKit job so a local terminal reports
        # exactly which voice provider still needs configuration.
        get_settings().require_agent_providers()
        cli.run_app(server)
    except MissingConfigurationError as error:
        logger.error("configuration_error %s", error)
        raise SystemExit(2) from error
