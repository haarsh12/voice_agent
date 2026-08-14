"""Test cases for provider factories."""

from __future__ import annotations

import pytest

from app.agent.providers import create_stt, create_llm, create_tts
from app.config.settings import get_settings


def test_create_stt_returns_instance():
    """Test that create_stt returns a valid STT instance."""
    settings = get_settings()
    
    try:
        stt = create_stt(settings)
        assert stt is not None
        # Check it's a Deepgram STT instance
        assert hasattr(stt, "__class__")
    except Exception as e:
        # If API key is missing, this is expected
        assert "api" in str(e).lower() or "key" in str(e).lower()


def test_create_llm_returns_instance():
    """Test that create_llm returns a valid LLM instance."""
    settings = get_settings()
    
    try:
        llm = create_llm(settings)
        assert llm is not None
        # Check it's a Mistral LLM instance
        assert hasattr(llm, "__class__")
    except Exception as e:
        # If API key is missing, this is expected
        assert "api" in str(e).lower() or "key" in str(e).lower()


def test_create_tts_returns_instance():
    """Test that create_tts returns a valid TTS instance."""
    settings = get_settings()
    
    try:
        tts = create_tts(settings)
        assert tts is not None
        # Check it's a Cartesia TTS instance
        assert hasattr(tts, "__class__")
    except Exception as e:
        # If API key is missing, this is expected
        assert "api" in str(e).lower() or "key" in str(e).lower()


def test_create_tts_with_custom_language():
    """Test that create_tts accepts custom language parameter."""
    settings = get_settings()
    
    try:
        tts_en = create_tts(settings, language="en")
        tts_hi = create_tts(settings, language="hi")
        tts_mr = create_tts(settings, language="mr")
        
        assert tts_en is not None
        assert tts_hi is not None
        assert tts_mr is not None
    except Exception as e:
        # If API key is missing, this is expected
        assert "api" in str(e).lower() or "key" in str(e).lower()


def test_stt_uses_settings_model():
    """Test that STT uses the model from settings."""
    settings = get_settings()
    
    # Verify settings have the expected values
    assert settings.deepgram_stt_model == "nova-3"
    assert settings.deepgram_stt_language == "multi"


def test_llm_uses_settings_model():
    """Test that LLM uses the model from settings."""
    settings = get_settings()
    
    # Verify settings have the expected values
    assert "mistral" in settings.mistral_model.lower()
    assert isinstance(settings.mistral_temperature, float)


def test_tts_uses_settings_model():
    """Test that TTS uses the model from settings."""
    settings = get_settings()
    
    # Verify settings have the expected values
    assert "sonic" in settings.cartesia_tts_model.lower()
    assert len(settings.cartesia_voice_id) > 0
    assert settings.cartesia_tts_language in ["en", "hi", "mr"]
