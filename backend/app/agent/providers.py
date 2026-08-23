"""Provider factories keep the STT, LLM, and TTS choices independently swappable."""

from __future__ import annotations

from google.genai.types import HttpOptions
from livekit.plugins import google

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
    """Create Google Cloud TTS with Chirp 3 HD voices for streaming.
    
    **IMPORTANT**: Only Chirp 3: HD voices support streaming synthesis in LiveKit!
    Neural2 and Wavenet voices do NOT work with streaming.
    
    Voice Selection (Chirp 3: HD - Based on Official Google Documentation):
    Female voices: Kore, Aoede, Despina, Achernar, Callirrhoe, Erinome, etc.
    Male voices: Charon, Puck, Fenrir, Enceladus, Achird, etc.
    
    Args:
        settings: Application settings with Google Cloud credentials
        language: Language code (hi, mr, en) for voice selection
    
    Returns:
        Google Cloud TTS instance configured with Chirp 3: HD voice
    """
    
    # Map language codes to Chirp 3: HD FEMALE voices
    # Chirp 3: HD voice naming: <locale>-Chirp3-HD-<character>
    # Using Kore (Female) as default voice across all languages
    voice_map = {
        "hi": "hi-IN-Chirp3-HD-Kore",       # Hindi Female
        "hi-IN": "hi-IN-Chirp3-HD-Kore",
        "mr": "mr-IN-Chirp3-HD-Kore",       # Marathi Female (Native support!)
        "mr-IN": "mr-IN-Chirp3-HD-Kore",
        "en": "en-US-Chirp3-HD-Kore",       # English Female
        "en-IN": "en-US-Chirp3-HD-Kore",
        "en-US": "en-US-Chirp3-HD-Kore",
    }
    
    # Language code mapping for the `language` parameter
    language_map = {
        "hi": "hi-IN",
        "mr": "mr-IN",       # Marathi has native support!
        "en": "en-US",
        "hi-IN": "hi-IN",
        "mr-IN": "mr-IN",
        "en-IN": "en-US",
        "en-US": "en-US",
    }
    
    # Use provided language or default from settings
    lang_code = language or settings.google_tts_language
    selected_voice_name = voice_map.get(lang_code, "mr-IN-Chirp3-HD-Kore")
    selected_language = language_map.get(lang_code, "mr-IN")
    
    return google.TTS(
        language=selected_language,
        voice_name=selected_voice_name,
        model_name="chirp_3",  # REQUIRED for Chirp 3: HD voices
        speaking_rate=settings.google_tts_speed,
        pitch=settings.google_tts_pitch,
        credentials_file=settings.google_application_credentials,
        use_streaming=True,  # Enable streaming synthesis
    )
