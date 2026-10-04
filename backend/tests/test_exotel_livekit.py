"""Unit tests for the offline Exotel-to-LiveKit configuration plan."""

from __future__ import annotations

from app.config.settings import Settings
from app.core.client_device import ClientDevice, LIVEKIT_DEVICE_ATTRIBUTE
from app.telephony.livekit_exotel import (
    desired_dispatch_rule,
    desired_inbound_trunk,
    management_url,
)


def _settings() -> Settings:
    return Settings(
        livekit_url="wss://sample.livekit.cloud",
        livekit_api_key="test-key",
        livekit_api_secret="test-secret",
        exotel_exophone_e164="+912048565978",
    )


def test_management_url_uses_https_for_livekit_server_api() -> None:
    assert management_url("wss://sample.livekit.cloud") == "https://sample.livekit.cloud"


def test_exotel_trunk_is_bound_to_one_e164_exophone() -> None:
    trunk = desired_inbound_trunk(_settings())
    assert trunk.name == "sahayak-exotel-inbound"
    assert list(trunk.numbers) == ["+912048565978"]


def test_exotel_dispatch_isolated_and_marks_the_sip_participant() -> None:
    rule = desired_dispatch_rule(_settings(), "ST_test")
    assert list(rule.trunk_ids) == ["ST_test"]
    assert rule.hide_phone_number is True
    assert dict(rule.attributes) == {LIVEKIT_DEVICE_ATTRIBUTE: ClientDevice.EXOTEL.value}
    assert rule.rule.dispatch_rule_callee.randomize is True
    assert rule.rule.dispatch_rule_callee.room_prefix == "sahayak-call-"
    assert rule.room_config.agents[0].agent_name == "sahayak-ai"
