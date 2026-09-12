"""Regression coverage for the browser-to-agent language protocol."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.agent.languages import stt_languages_for_model, voice_for_language
from app.agent.runner import strip_internal_voice_markup
from app.agent import providers
from app.api import routes
from app.services.token_issuer import IssuedToken


async def _chunks(*values: str) -> AsyncIterator[str]:
    for value in values:
        yield value


async def _collect(*values: str) -> str:
    return "".join(
        [chunk async for chunk in strip_internal_voice_markup(_chunks(*values))]
    )


def test_all_selector_languages_have_a_matching_stt_and_tts_profile() -> None:
    expected_stt_codes = {
        "hi-IN": "hi-IN",
        "mr-IN": "mr-IN",
        "en-IN": "en-IN",
        "ta-IN": "ta-IN",
        "te-IN": "te-IN",
        "kn-IN": "kn-IN",
        "ml-IN": "ml-IN",
        "gu-IN": "gu-IN",
        "bn-IN": "bn-IN",
        "pa-IN": "pa-IN",
    }

    assert {language: list(stt_languages_for_model(language, "latest_long")) for language in expected_stt_codes} == {
        language: [stt_code] for language, stt_code in expected_stt_codes.items()
    }
    assert all(
        voice_for_language(language).startswith(f"{language}-Chirp3-HD-")
        for language in expected_stt_codes
    )
    assert stt_languages_for_model("pa-IN", "chirp_3") == ["pa-Guru-IN"]


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


def test_chirp3_stt_does_not_enable_unsupported_spoken_punctuation(monkeypatch) -> None:
    received: dict[str, object] = {}

    def fake_stt(**kwargs):
        received.update(kwargs)
        return object()

    settings = type(
        "SpeechSettings",
        (),
        {
            "google_stt_language": "hi-IN",
            "google_stt_model": "chirp_3",
            "google_stt_location": "us",
            "google_application_credentials": None,
            "keyterms": [],
        },
    )()
    monkeypatch.setattr(providers.google, "STT", fake_stt)

    providers.create_stt(settings, primary_language="ta-IN")

    assert received["spoken_punctuation"] is False
    assert received["languages"] == ["ta-IN"]
    assert received["detect_language"] is False


def test_internal_reasoning_never_reaches_tts_when_tags_are_streamed_in_pieces() -> None:
    spoken = asyncio.run(
        _collect("Hello <tho", "ught>do not say this</thought> world")
    )

    assert spoken == "Hello  world"
