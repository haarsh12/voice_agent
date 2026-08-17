"""Provider factories keep the STT, LLM, and TTS choices independently swappable."""

from __future__ import annotations

from google.genai.types import HttpOptions
from livekit.plugins import cartesia, google

from app.config.settings import Settings
from app.services.gemini import load_vertex_authentication


def create_stt(settings: Settings) -> google.STT:
    """Create streaming Google Cloud STT with multilingual support.
    
    Supports Hindi (hi-IN), Marathi (mr-IN), and English (en-IN/en-US).
    Primary language set via GOOGLE_STT_LANGUAGE, with automatic code-switching.
    """

    # Convert keyterms list to keywords format: list of tuples (word, boost_value)
    keywords = [(term, 5.0) for term in settings.keyterms] if settings.keyterms else None

    # Support multiple languages for code-switching between Hindi/Marathi/English
    # Primary language from settings, with fallback alternates
    languages = [settings.google_stt_language]
    
    # Add alternate languages for seamless code-switching
    if settings.google_stt_language == "hi-IN":
        languages.extend(["mr-IN", "en-IN"])
    elif settings.google_stt_language == "mr-IN":
        languages.extend(["hi-IN", "en-IN"])
    elif settings.google_stt_language.startswith("en"):
        languages.extend(["hi-IN", "mr-IN"])

    return google.STT(
        languages=languages,
        model=settings.google_stt_model,
        spoken_punctuation=True,
        keywords=keywords,
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


def create_tts(settings: Settings, *, language: str | None = None) -> cartesia.TTS:
    """Create Cartesia Sonic; language may be updated between user turns."""

    return cartesia.TTS(
        model=settings.cartesia_tts_model,
        voice=settings.cartesia_voice_id,
        language=language or settings.cartesia_tts_language,
        speed=settings.cartesia_tts_speed,
    )
