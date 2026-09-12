"""Provider factories keep the STT, LLM, and TTS choices independently swappable."""

from __future__ import annotations

from google.genai.types import HttpOptions
from livekit.plugins import google

from app.agent.languages import (
    normalize_language,
    stt_languages_for_model,
    voice_for_language,
)
from app.config.settings import Settings
from app.services.gemini import load_vertex_authentication


def _resolve_language(language: str | None, fallback: str) -> str:
    """Resolve configuration and remote data to one of our supported locales."""

    return normalize_language(language) or normalize_language(fallback) or "hi-IN"


def create_stt(settings: Settings, *, primary_language: str | None = None) -> google.STT:
    """Create streaming STT locked to the language selected in the browser."""

    selected_language = _resolve_language(primary_language, settings.google_stt_language)

    return google.STT(
        languages=stt_languages_for_model(selected_language, settings.google_stt_model),
        model=settings.google_stt_model,
        location=settings.google_stt_location,
        detect_language=False,
        punctuate=True,
        spoken_punctuation=False,
        enable_word_time_offsets=False,
        # Do not pass speech-adaptation/keyterm options in this explicit-
        # language path; they are unnecessary and caused V2 request failures.
        credentials_file=settings.google_application_credentials,
    )


def create_llm(settings: Settings) -> google.LLM:
    """Create Gemini via the supported Google Gen AI SDK on Vertex AI."""

    auth = load_vertex_authentication(settings)
    return google.LLM(
        model=settings.gemini_model,
        vertexai=True,
        project=auth.project_id,
        location=settings.google_cloud_location,
        credentials=auth.credentials,
        temperature=settings.gemini_temperature,
        http_options=HttpOptions(api_version="v1"),
    )


def create_tts(settings: Settings, *, language: str | None = None) -> google.TTS:
    """Create a streaming Chirp 3 HD voice for the selected locale."""

    selected_language = _resolve_language(language, settings.google_tts_language)
    return google.TTS(
        language=selected_language,
        voice_name=voice_for_language(selected_language),
        model_name="chirp_3",
        speaking_rate=settings.google_tts_speed,
        pitch=settings.google_tts_pitch,
        credentials_file=settings.google_application_credentials,
        use_streaming=True,
    )


def update_stt_language(stt: google.STT, *, language: str, model: str) -> str:
    """Update an active recognizer without interrupting its voice session."""

    selected_language = _resolve_language(language, "hi-IN")
    stt.update_options(
        languages=stt_languages_for_model(selected_language, model),
        detect_language=False,
    )
    return selected_language


def update_tts_language(tts: google.TTS, *, language: str) -> str:
    """Update an active synthesizer for the next speech segment."""

    selected_language = _resolve_language(language, "hi-IN")
    tts.update_options(
        language=selected_language,
        voice_name=voice_for_language(selected_language),
    )
    return selected_language
