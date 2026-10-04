"""Trusted parsing and presentation policy for Sahayak client devices.

The device declaration is intentionally a UX and delivery hint only.  It must
never be used as an authentication or authorization signal: an HTTP caller can
set any header and SIP participant attributes originate outside this process.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException, Request, status


DEVICE_HEADER = "X-Sahayak-Device"
TOKEN_DEVICE_QUERY_PARAMETER = "client_device"
LIVEKIT_DEVICE_ATTRIBUTE = "sahayak.device"


class ClientDevice(StrEnum):
    """The supported Sahayak interaction surfaces."""

    RASPBERRY_PI = "raspberry-pi"
    MOBILE_APP = "mobile-app"
    WEBSITE = "website"
    ESP32 = "esp32"
    EXOTEL = "exotel"


@dataclass(frozen=True, slots=True)
class ClientDeviceContext:
    """A validated device declaration, if the caller supplied one."""

    device: ClientDevice | None
    declared: bool

    @property
    def value(self) -> str:
        return self.device.value if self.device is not None else "unknown"


class InvalidClientDevice(ValueError):
    """Raised when a caller attempts to use an unsupported device value."""


def parse_client_device(value: object) -> ClientDevice | None:
    """Normalize one bounded device value without guessing from user agents."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidClientDevice("device must be text")
    normalized = value.strip().lower()
    if not normalized:
        return None
    try:
        return ClientDevice(normalized)
    except ValueError as error:
        supported = ", ".join(item.value for item in ClientDevice)
        raise InvalidClientDevice(f"unsupported device; use one of: {supported}") from error


def device_context_from_request(
    request: Request,
    *,
    allow_query_fallback: bool = False,
) -> ClientDeviceContext:
    """Read the standard header, with a token-endpoint query fallback.

    LiveKit's browser TokenSource controls its own request headers.  The query
    fallback is restricted to that endpoint by the caller and exists only so a
    website can still declare its device while that SDK obtains a token.
    """

    header_value = request.headers.get(DEVICE_HEADER)
    query_value = request.query_params.get(TOKEN_DEVICE_QUERY_PARAMETER)
    if query_value is not None and not allow_query_fallback:
        raise InvalidClientDevice(
            f"{TOKEN_DEVICE_QUERY_PARAMETER} is only allowed when requesting a LiveKit token"
        )
    if header_value and query_value and header_value.strip().lower() != query_value.strip().lower():
        raise InvalidClientDevice("header and query device declarations disagree")
    raw_value = header_value if header_value is not None else query_value
    device = parse_client_device(raw_value)
    return ClientDeviceContext(device=device, declared=device is not None)


def get_client_device_context(request: Request) -> ClientDeviceContext:
    """FastAPI dependency for routes whose AI behavior depends on the device."""

    stored = getattr(request.state, "client_device_context", None)
    if isinstance(stored, ClientDeviceContext):
        return stored
    try:
        context = device_context_from_request(request)
    except InvalidClientDevice as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    request.state.client_device_context = context
    return context


def device_response_guidance(device: ClientDevice | None) -> str:
    """Return small, model-safe response constraints for a device surface."""

    guidance = {
        ClientDevice.RASPBERRY_PI: (
            "The user is on a Raspberry Pi voice-first device. Use short, "
            "speakable sentences and do not rely on a screen or links."
        ),
        ClientDevice.MOBILE_APP: (
            "The user is in the mobile app. Keep answers touch-friendly and "
            "brief; visual citations may be shown by the app separately."
        ),
        ClientDevice.WEBSITE: (
            "The user is on the website. Keep answers concise; the website "
            "may show backend-provided citations separately."
        ),
        ClientDevice.ESP32: (
            "The user is on an ESP32 constrained device. Return plain text, "
            "no Markdown, no links, and at most two very short sentences."
        ),
        ClientDevice.EXOTEL: (
            "The user is on an Exotel PSTN call. Speak naturally, never refer "
            "to a screen, link, button, upload, or visual citation, and keep "
            "each reply to two short sentences."
        ),
    }
    return guidance.get(
        device,
        "The client device is unknown. Give a concise answer without relying on a specific interface.",
    )
