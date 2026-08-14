"""Provider factories keep the STT, LLM, and TTS choices independently swappable."""

from __future__ import annotations

from livekit.plugins import cartesia, deepgram, mistralai

from app.config.settings import Settings


def create_stt(settings: Settings) -> deepgram.STT:
    """Create streaming Deepgram Nova-3 with official multilingual mode."""

    return deepgram.STT(
        model=settings.deepgram_stt_model,
        language=settings.deepgram_stt_language,
        keyterm=settings.keyterms,
    )


def create_llm(settings: Settings) -> mistralai.LLM:
    """Create Mistral's streaming chat integration for the voice pipeline."""

    return mistralai.LLM(
        model=settings.mistral_model,
        temperature=settings.mistral_temperature,
    )


def create_tts(settings: Settings, *, language: str | None = None) -> cartesia.TTS:
    """Create Cartesia Sonic; language may be updated between user turns."""

    return cartesia.TTS(
        model=settings.cartesia_tts_model,
        voice=settings.cartesia_voice_id,
        language=language or settings.cartesia_tts_language,
        speed=settings.cartesia_tts_speed,
    )
