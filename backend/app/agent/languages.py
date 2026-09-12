"""Language profiles shared by the realtime voice pipeline.

The browser deliberately uses a small, stable set of BCP-47 codes. Google
Speech-to-Text uses a more specific Punjabi code, so conversions live here
rather than being scattered through the room and provider code.
"""

from __future__ import annotations

from collections.abc import Sequence


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

# The UI keeps the familiar pa-IN identifier. Chirp 3 uses the more specific
# Gurmukhi identifier only when that model is explicitly selected.
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


def normalize_language(value: object) -> str | None:
    """Return a supported UI language code, or ``None`` for untrusted input."""

    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if candidate in SUPPORTED_LANGUAGE_CODES:
        return candidate
    return _ALIASES.get(candidate)


def stt_languages_for_model(preferred_language: str, model: str) -> Sequence[str]:
    """Return one explicit, valid locale for the selected recognizer model.

    Auto-detection is intentionally disabled. One selected language is the
    reliable mode supported by the selector and avoids provider-specific
    multi-language request limits.
    """

    normalized = normalize_language(preferred_language)
    if normalized is None:
        raise ValueError("preferred_language must be supported")
    stt_language = "pa-Guru-IN" if model == "chirp_3" and normalized == "pa-IN" else normalized
    return [stt_language]


def voice_for_language(language: str) -> str:
    """Return the documented Chirp 3 HD voice for a supported locale."""

    normalized = normalize_language(language)
    if normalized is None:
        raise ValueError("language must be supported")
    return CHIRP3_VOICES[normalized]
