"""Test cases for settings and configuration."""

from __future__ import annotations

import pytest

from app.config.settings import Settings, MissingConfigurationError, get_settings


def test_settings_can_be_loaded():
    """Test that settings can be loaded without errors."""
    settings = get_settings()
    assert settings is not None
    assert isinstance(settings, Settings)


def test_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_has_required_attributes():
    """Test that settings has all required attributes."""
    settings = get_settings()
    
    assert hasattr(settings, "api_host")
    assert hasattr(settings, "api_port")
    assert hasattr(settings, "cors_origins")
    assert hasattr(settings, "livekit_url")
    assert hasattr(settings, "agent_name")
    assert hasattr(settings, "google_stt_model")
    assert hasattr(settings, "gemini_model")
    assert hasattr(settings, "cartesia_tts_model")


def test_settings_default_values():
    """Test that settings have sensible default values."""
    settings = Settings(
        google_stt_model="latest_long",
        google_stt_language="en-US",
        gemini_temperature=0.35,
    )
    
    assert settings.api_host in ["127.0.0.1", "0.0.0.0"]
    assert settings.api_port > 0
    assert settings.agent_name == "vyamit-voice"
    assert settings.google_stt_model == "latest_long"
    assert settings.google_stt_language == "en-US"
    assert settings.gemini_temperature >= 0 and settings.gemini_temperature <= 2


def test_allowed_origins_property():
    """Test that allowed_origins property parses CORS origins correctly."""
    settings = get_settings()
    origins = settings.allowed_origins
    
    assert isinstance(origins, list)
    assert len(origins) > 0
    # Should have localhost origins
    assert any("localhost" in origin for origin in origins)


def test_keyterms_property():
    """Test that keyterms property parses correctly."""
    settings = get_settings()
    keyterms = settings.keyterms
    
    assert isinstance(keyterms, list)
    # Should have at least "Vyamit"
    if keyterms:
        assert isinstance(keyterms[0], str)


def test_token_issuer_configured_property():
    """Test token_issuer_configured property."""
    settings = get_settings()
    
    # Should return a boolean
    assert isinstance(settings.token_issuer_configured, bool)


def test_agent_providers_configured_property():
    """Test agent_providers_configured property."""
    settings = get_settings()
    
    # Should return a boolean
    assert isinstance(settings.agent_providers_configured, bool)


def test_require_token_issuer_with_missing_config():
    """Test that require_token_issuer raises error when config is missing."""
    settings = Settings(
        livekit_url="",
        livekit_api_key=None,
        livekit_api_secret=None
    )
    
    with pytest.raises(MissingConfigurationError):
        settings.require_token_issuer()


def test_temperature_validation_range():
    """Test that temperature is within valid range."""
    settings = get_settings()
    
    assert 0 <= settings.gemini_temperature <= 2


def test_tts_speed_validation_range():
    """Test that TTS speed is within valid range."""
    settings = get_settings()
    
    assert 0.6 <= settings.cartesia_tts_speed <= 1.5


def test_noise_cancellation_flag():
    """Test enhanced noise cancellation flag."""
    settings = get_settings()
    
    assert isinstance(settings.enable_enhanced_noise_cancellation, bool)
