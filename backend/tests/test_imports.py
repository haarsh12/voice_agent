"""Test cases to verify all modules can be imported."""

from __future__ import annotations

import pytest


def test_import_main_app():
    """Test that main FastAPI app can be imported."""
    from app.main import app
    assert app is not None


def test_import_settings():
    """Test that settings module can be imported."""
    from app.config.settings import Settings, get_settings
    assert Settings is not None
    assert get_settings is not None


def test_import_routes():
    """Test that API routes can be imported."""
    from app.api.routes import router
    assert router is not None


def test_import_token_issuer():
    """Test that token issuer can be imported."""
    from app.services.token_issuer import issue_browser_token, IssuedToken
    assert issue_browser_token is not None
    assert IssuedToken is not None


def test_import_providers():
    """Test that provider factories can be imported."""
    from app.agent.providers import create_stt, create_llm, create_tts
    assert create_stt is not None
    assert create_llm is not None
    assert create_tts is not None


def test_import_prompts():
    """Test that prompts module can be imported."""
    from app.agent.prompts import VOICE_ASSISTANT_INSTRUCTIONS
    assert VOICE_ASSISTANT_INSTRUCTIONS is not None
    assert isinstance(VOICE_ASSISTANT_INSTRUCTIONS, str)
    assert len(VOICE_ASSISTANT_INSTRUCTIONS) > 0


def test_import_runner():
    """Test that agent runner can be imported."""
    from app.agent.runner import server, VyamitAssistant
    assert server is not None
    assert VyamitAssistant is not None


def test_import_logging():
    """Test that logging module can be imported."""
    from app.core.logging import configure_logging
    assert configure_logging is not None


def test_all_app_submodules():
    """Test that all app submodules exist and can be imported."""
    import app
    import app.api
    import app.config
    import app.core
    import app.services
    import app.agent
    
    assert app is not None
    assert app.api is not None
    assert app.config is not None
    assert app.core is not None
    assert app.services is not None
    assert app.agent is not None
