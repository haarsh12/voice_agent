"""Idempotent LiveKit configuration for Exotel inbound PSTN calls.

This module creates one reusable inbound trunk and one reusable dispatch rule.
It never runs automatically at API startup, so normal backend execution cannot
silently modify LiveKit Cloud configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from livekit import api

from app.config.settings import Settings
from app.core.client_device import ClientDevice, LIVEKIT_DEVICE_ATTRIBUTE


@dataclass(frozen=True, slots=True)
class ExotelLiveKitResources:
    """Identifiers reported after a dry-run or applied configuration sync."""

    trunk_id: str
    dispatch_rule_id: str
    changed: bool


def management_url(livekit_url: str) -> str:
    """Convert a WebRTC URL into the HTTPS URL required by LiveKit's API."""

    parsed = urlparse(livekit_url.strip())
    scheme = {"wss": "https", "ws": "http"}.get(parsed.scheme, parsed.scheme)
    if scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("LIVEKIT_URL must be an http(s) or ws(s) URL with a hostname.")
    return urlunparse((scheme, parsed.netloc, parsed.path, "", "", ""))


def desired_inbound_trunk(settings: Settings) -> api.SIPInboundTrunkInfo:
    """Describe the one Exotel DID accepted by LiveKit."""

    return api.SIPInboundTrunkInfo(
        name=settings.exotel_livekit_trunk_name,
        numbers=[settings.exotel_exophone_e164],
        metadata='{"integration":"exotel","managed_by":"sahayak"}',
    )


def desired_dispatch_rule(settings: Settings, trunk_id: str) -> api.SIPDispatchRuleInfo:
    """Describe isolated, PII-minimizing rooms for Exotel SIP calls."""

    # A randomized callee rule makes a unique room per call without putting the
    # caller's phone number into a room name.  ``hide_phone_number`` also keeps
    # caller ID from ordinary room participants.
    rule = api.SIPDispatchRule(
        dispatch_rule_callee=api.SIPDispatchRuleCallee(
            room_prefix="sahayak-call-",
            randomize=True,
        )
    )
    return api.SIPDispatchRuleInfo(
        name=settings.exotel_livekit_dispatch_rule_name,
        trunk_ids=[trunk_id],
        hide_phone_number=True,
        attributes={LIVEKIT_DEVICE_ATTRIBUTE: ClientDevice.EXOTEL.value},
        metadata='{"integration":"exotel","managed_by":"sahayak"}',
        rule=rule,
        room_config=api.RoomConfiguration(
            agents=[api.RoomAgentDispatch(agent_name=settings.agent_name)]
        ),
    )


def _one_matching(items: list[object], *, name: str, label: str) -> object | None:
    matching = [item for item in items if getattr(item, "name", None) == name]
    if len(matching) > 1:
        raise RuntimeError(f"More than one {label} is named {name!r}; resolve the duplicate manually.")
    return matching[0] if matching else None


async def sync_exotel_livekit(settings: Settings, *, apply: bool) -> ExotelLiveKitResources:
    """Plan or apply the intended reusable trunk and dispatch rule.

    ``apply=False`` performs the same reads but does not make any external
    changes.  This keeps the setup command safe to run before granting it
    authority to create or update LiveKit resources.
    """

    settings.require_exotel_livekit_configuration()
    client = api.LiveKitAPI(
        management_url(settings.livekit_url),
        settings.livekit_api_key.get_secret_value(),
        settings.livekit_api_secret.get_secret_value(),
    )
    changed = False
    try:
        existing_trunks = await client.sip.list_inbound_trunk(api.ListSIPInboundTrunkRequest())
        trunk = _one_matching(
            list(existing_trunks.items),
            name=settings.exotel_livekit_trunk_name,
            label="inbound trunk",
        )
        trunk_changed = trunk is None or list(trunk.numbers) != [settings.exotel_exophone_e164]
        if trunk_changed:
            changed = True
            if apply:
                if trunk is None:
                    trunk = await client.sip.create_inbound_trunk(
                        api.CreateSIPInboundTrunkRequest(trunk=desired_inbound_trunk(settings))
                    )
                else:
                    trunk = await client.sip.update_inbound_trunk_fields(
                        trunk.sip_trunk_id,
                        numbers=[settings.exotel_exophone_e164],
                    )
        if trunk is None:
            return ExotelLiveKitResources(trunk_id="(will be created)", dispatch_rule_id="(pending)", changed=True)

        expected_rule = desired_dispatch_rule(settings, trunk.sip_trunk_id)
        existing_rules = await client.sip.list_dispatch_rule(api.ListSIPDispatchRuleRequest())
        dispatch_rule = _one_matching(
            list(existing_rules.items),
            name=settings.exotel_livekit_dispatch_rule_name,
            label="SIP dispatch rule",
        )
        dispatch_changed = (
            dispatch_rule is None
            or list(dispatch_rule.trunk_ids) != [trunk.sip_trunk_id]
            or bool(dispatch_rule.hide_phone_number) is not True
            or dict(dispatch_rule.attributes) != dict(expected_rule.attributes)
            or dispatch_rule.rule != expected_rule.rule
            or dispatch_rule.room_config != expected_rule.room_config
        )
        if dispatch_changed:
            changed = True
            if apply:
                if dispatch_rule is None:
                    dispatch_rule = await client.sip.create_dispatch_rule(
                        api.CreateSIPDispatchRuleRequest(dispatch_rule=expected_rule)
                    )
                else:
                    dispatch_rule = await client.sip.update_dispatch_rule(
                        dispatch_rule.sip_dispatch_rule_id,
                        expected_rule,
                    )
        if dispatch_rule is None:
            return ExotelLiveKitResources(
                trunk_id=trunk.sip_trunk_id,
                dispatch_rule_id="(will be created)",
                changed=True,
            )
        return ExotelLiveKitResources(
            trunk_id=trunk.sip_trunk_id,
            dispatch_rule_id=dispatch_rule.sip_dispatch_rule_id,
            changed=changed,
        )
    finally:
        await client.aclose()
