"""Language profiles shared by the realtime voice pipeline.

The browser deliberately uses a small, stable set of BCP-47 codes. Google
Speech-to-Text uses a more specific Punjabi code, so conversions live here
rather than being scattered through the room and provider code.
"""

from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_LANGUAGE_CODES: tuple[str, ...] = (
    "hi-IN",
    "mr-IN",
    "en-IN",
    "ta-IN",
    "te-IN",
    "kn-IN",
    "ml-IN",
    "gu-IN",
    "bn-IN",
    "pa-IN",
)

LANGUAGE_NAMES: dict[str, str] = {
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "en-IN": "English (India)",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "gu-IN": "Gujarati",
    "bn-IN": "Bengali",
    "pa-IN": "Punjabi",
}

# The UI keeps the familiar pa-IN identifier. Google Speech-to-Text V1 uses
# the more specific Gurmukhi identifier for Punjabi.
_ALIASES: dict[str, str] = {
    "hi": "hi-IN",
    "mr": "mr-IN",
    "en": "en-IN",
    "en-US": "en-IN",
    "en-GB": "en-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "pa": "pa-IN",
    "pa-Guru-IN": "pa-IN",
}

# Locale-specific Chirp 3 HD female voices. An explicit map prevents a locale
# update from silently retaining the previous language's voice.
CHIRP3_VOICES: dict[str, str] = {
    language: f"{language}-Chirp3-HD-Aoede" for language in SUPPORTED_LANGUAGE_CODES
}


@dataclass(frozen=True)
class STTProfile:
    """A Google STT V1 configuration known to support one UI language."""

    locale: str
    model: str


# Do not infer these values from the browser locale.  Google publishes model
# support per locale, and `latest_long` is *not* available for Bengali,
# Gujarati, or Punjabi.  Sending an unsupported locale/model combination
# terminates the realtime STT stream, which in turn leaves the UI with no
# transcript or reply.  `default` is the documented compatible V1 model for
# those three languages.  Punjabi also requires its script-specific locale.
STT_PROFILES: dict[str, STTProfile] = {
    "hi-IN": STTProfile(locale="hi-IN", model="latest_long"),
    "mr-IN": STTProfile(locale="mr-IN", model="latest_long"),
    "en-IN": STTProfile(locale="en-IN", model="latest_long"),
    "ta-IN": STTProfile(locale="ta-IN", model="latest_long"),
    "te-IN": STTProfile(locale="te-IN", model="latest_long"),
    "kn-IN": STTProfile(locale="kn-IN", model="latest_long"),
    "ml-IN": STTProfile(locale="ml-IN", model="latest_long"),
    "gu-IN": STTProfile(locale="gu-IN", model="default"),
    "bn-IN": STTProfile(locale="bn-IN", model="default"),
    "pa-IN": STTProfile(locale="pa-Guru-IN", model="default"),
}


def normalize_language(value: object) -> str | None:
    """Return a supported UI language code, or ``None`` for untrusted input."""

    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if candidate in SUPPORTED_LANGUAGE_CODES:
        return candidate
    return _ALIASES.get(candidate)


def stt_profile_for_language(language: str) -> STTProfile:
    """Return the supported, single-language STT profile for ``language``.

    Auto-detection is intentionally disabled.  One selected language keeps
    Google requests within the provider's language limits and makes the
    resulting transcript match the selected script.
    """

    normalized = normalize_language(language)
    if normalized is None:
        raise ValueError("language must be supported")
    return STT_PROFILES[normalized]


def voice_for_language(language: str) -> str:
    """Return the documented Chirp 3 HD voice for a supported locale."""

    normalized = normalize_language(language)
    if normalized is None:
        raise ValueError("language must be supported")
    return CHIRP3_VOICES[normalized]
