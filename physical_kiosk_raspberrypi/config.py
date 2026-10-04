# Sahayak AI — Raspberry Pi Kiosk Hardware Configuration
# All settings are loaded from config.env; no credentials are hard-coded here.

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_env_file(filename: str = "config.env") -> None:
    """Parse key=value pairs from an env file into os.environ."""
    for candidate in (BASE_DIR / filename, BASE_DIR / ".env"):
        if candidate.exists():
            with open(candidate, encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))
            break


load_env_file()

# ── Resolve relative Google credentials path ───────────────────────────────
_g_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
if _g_creds and not os.path.isabs(_g_creds):
    _abs = str(BASE_DIR / _g_creds)
    if os.path.exists(_abs):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _abs

# ── Backend / Server ────────────────────────────────────────────────────────
HOST: str = os.environ.get("KIOSK_HOST", "0.0.0.0")
PORT: int = int(os.environ.get("KIOSK_PORT", "5000"))
BACKEND_SERVER_URL: str = os.environ.get("BACKEND_SERVER_URL", "http://127.0.0.1:8000")

# ── LiveKit / Voice Agent ───────────────────────────────────────────────────
# The agent name must match the agent worker registration on the backend.
AGENT_NAME: str = os.environ.get("LIVEKIT_AGENT_NAME", "sahayak-ai")

# ── Audio ───────────────────────────────────────────────────────────────────
ALSA_RECORD_DEVICE: str = os.environ.get("ALSA_RECORD_DEVICE", "plughw:CARD=sndrpigooglevoi,DEV=0")
ALSA_PLAYBACK_DEVICE: str = os.environ.get("ALSA_PLAYBACK_DEVICE", "plughw:CARD=sndrpigooglevoi,DEV=0")
SAMPLE_RATE: int = int(os.environ.get("AUDIO_SAMPLE_RATE", "48000"))
CHANNELS: int = int(os.environ.get("AUDIO_CHANNELS", "2"))
BIT_DEPTH: str = os.environ.get("AUDIO_BIT_DEPTH", "S32_LE")
TARGET_SAMPLE_RATE: int = 16000  # Required by Google STT

# ── STT ─────────────────────────────────────────────────────────────────────
STT_LANGUAGE: str = os.environ.get("STT_LANGUAGE", "hi-IN")

# ── Camera ──────────────────────────────────────────────────────────────────
CAMERA_INDEX: int = int(os.environ.get("CAMERA_INDEX", "0"))
CAMERA_WIDTH: int = int(os.environ.get("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT: int = int(os.environ.get("CAMERA_HEIGHT", "480"))
CAMERA_FPS: int = int(os.environ.get("CAMERA_FPS", "30"))

# ── Storage ─────────────────────────────────────────────────────────────────
MODELS_DIR: str = str(BASE_DIR / "models")
DB_PATH: str = str(BASE_DIR / "data" / "users.db")
