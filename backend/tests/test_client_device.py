"""Regression coverage for the cross-client device declaration contract."""

from __future__ import annotations

from app.agent.prompts import build_voice_assistant_instructions
from app.core.client_device import ClientDevice, InvalidClientDevice, parse_client_device
from app.services.gemini import build_text_chat_prompt


def test_supported_device_values_are_normalized_without_user_agent_guessing() -> None:
    assert parse_client_device("  MOBILE-APP ") == ClientDevice.MOBILE_APP
    assert parse_client_device(None) is None
    try:
        parse_client_device("desktop")
    except InvalidClientDevice as error:
        assert "unsupported device" in str(error)
    else:
        raise AssertionError("unsupported device values must be rejected")


def test_exotel_prompt_is_voice_only() -> None:
    prompt = build_voice_assistant_instructions("Hindi", client_device=ClientDevice.EXOTEL)
    assert "Exotel PSTN call" in prompt
    assert "never refer to a screen" in prompt


def test_esp32_text_prompt_is_constrained_for_a_small_device() -> None:
    prompt = build_text_chat_prompt(
        message="What should I do?",
        language="en-IN",
        client_device=ClientDevice.ESP32,
    )
    assert "ESP32 constrained device" in prompt
    assert "no Markdown" in prompt


def test_api_rejects_an_invalid_declared_device(client) -> None:
    response = client.get("/api/health", headers={"X-Sahayak-Device": "unknown-tablet"})
    assert response.status_code == 422
    assert "unsupported device" in response.json()["detail"]


def test_api_allows_a_missing_device_for_backwards_compatible_local_development(client) -> None:
    assert client.get("/api/health").status_code == 200


def test_device_query_parameter_is_limited_to_token_endpoint(client) -> None:
    response = client.get("/api/health?client_device=website")

    assert response.status_code == 422
