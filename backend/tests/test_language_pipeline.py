"""Regression coverage for the browser-to-agent language protocol."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.agent.languages import stt_profile_for_language, voice_for_language
from app.agent.runner import strip_internal_voice_markup
from app.agent import providers
from app.api import routes
from app.services.guest_sessions import guest_sessions
from app.services.token_issuer import IssuedToken


async def _chunks(*values: str) -> AsyncIterator[str]:
    for value in values:
        yield value


async def _collect(*values: str) -> str:
    return "".join(
        [chunk async for chunk in strip_internal_voice_markup(_chunks(*values))]
    )


def test_all_selector_languages_have_a_matching_stt_and_tts_profile() -> None:
    expected_stt_profiles = {
        "hi-IN": ("hi-IN", "latest_long"),
        "mr-IN": ("mr-IN", "latest_long"),
        "en-IN": ("en-IN", "latest_long"),
        "ta-IN": ("ta-IN", "latest_long"),
        "te-IN": ("te-IN", "latest_long"),
        "kn-IN": ("kn-IN", "latest_long"),
        "ml-IN": ("ml-IN", "latest_long"),
        "gu-IN": ("gu-IN", "default"),
        "bn-IN": ("bn-IN", "default"),
        "pa-IN": ("pa-Guru-IN", "default"),
    }

    assert {
        language: (profile.locale, profile.model)
        for language in expected_stt_profiles
        for profile in [stt_profile_for_language(language)]
    } == expected_stt_profiles
    assert all(
        voice_for_language(language).startswith(f"{language}-Chirp3-HD-")
        for language in expected_stt_profiles
    )


def test_live_stt_switch_updates_model_and_provider_locale() -> None:
    received: dict[str, object] = {}

    class FakeSTT:
        def update_options(self, **kwargs: object) -> None:
            received.update(kwargs)

    providers.update_stt_language(FakeSTT(), language="pa-IN")  # type: ignore[arg-type]

    assert received == {
        "languages": ["pa-Guru-IN"],
        "model": "default",
        "detect_language": False,
        "punctuate": False,
        "spoken_punctuation": False,
    }


def test_token_endpoint_uses_livekit_participant_language_attribute(monkeypatch) -> None:
    received: dict[str, object] = {}

    def fake_issue_browser_token(_settings, **kwargs):
        received.update(kwargs)
        return IssuedToken(server_url="wss://example.invalid", participant_token="test-token")

    settings = type("TokenSettings", (), {"require_token_issuer": lambda self: None})()
    monkeypatch.setattr(routes, "issue_browser_token", fake_issue_browser_token)

    response = asyncio.run(
        routes.create_token(
            routes.TokenRequest.model_validate(
                {"participant_attributes": {"language": "ta-IN"}}
            ),
            settings,
        )
    )

    assert response.server_url == "wss://example.invalid"
    assert received["language"] == "ta-IN"


def test_token_endpoint_binds_an_active_guest_context_capability(monkeypatch) -> None:
    received: dict[str, object] = {}
    session_id, session_secret = guest_sessions.create()

    def fake_issue_browser_token(_settings, **kwargs):
        received.update(kwargs)
        return IssuedToken(server_url="wss://example.invalid", participant_token="test-token")

    settings = type("TokenSettings", (), {"require_token_issuer": lambda self: None})()
    monkeypatch.setattr(routes, "issue_browser_token", fake_issue_browser_token)

    asyncio.run(
        routes.create_token(
            routes.TokenRequest.model_validate(
                {
                    "participant_attributes": {
                        "language": "hi-IN",
                        "guest_session_id": session_id,
                        "guest_session_secret": session_secret,
                    }
                }
            ),
            settings,
        )
    )

    assert received["guest_session_id"] == session_id
    assert received["guest_session_secret"] == session_secret


def test_stt_uses_the_selected_language_profile_without_unsupported_punctuation(monkeypatch) -> None:
    received: dict[str, object] = {}

    def fake_stt(**kwargs):
        received.update(kwargs)
        return object()

    settings = type(
        "SpeechSettings",
        (),
        {
            "google_stt_language": "hi-IN",
            "google_stt_model": "latest_long",
            "google_stt_location": "us",
            "google_application_credentials": None,
            "keyterms": [],
        },
    )()
    monkeypatch.setattr(providers.google, "STT", fake_stt)

    providers.create_stt(settings, primary_language="bn-IN")

    assert received["spoken_punctuation"] is False
    assert received["punctuate"] is False
    assert received["languages"] == ["bn-IN"]
    assert received["model"] == "default"
    assert received["detect_language"] is False


def test_tts_uses_the_selected_locale_and_voice_for_each_future_response(monkeypatch) -> None:
    received: dict[str, object] = {}

    def fake_tts(**kwargs: object) -> object:
        received.update(kwargs)
        return object()

    settings = type(
        "SpeechSettings",
        (),
        {
            "google_tts_language": "hi-IN",
            "google_tts_speed": 1.0,
            "google_tts_pitch": 0.0,
            "google_application_credentials": None,
        },
    )()
    monkeypatch.setattr(providers.google, "TTS", fake_tts)

    providers.create_tts(settings, language="gu-IN")

    assert received["language"] == "gu-IN"
    assert received["voice_name"] == "gu-IN-Chirp3-HD-Aoede"
    assert received["model_name"] == "chirp_3"
    assert received["use_streaming"] is True


def test_internal_reasoning_never_reaches_tts_when_tags_are_streamed_in_pieces() -> None:
    spoken = asyncio.run(
        _collect("Hello <tho", "ught>do not say this</thought> world")
    )

    assert spoken == "Hello  world"
