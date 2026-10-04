# Sahayak AI — Raspberry Pi Kiosk Configuration
# Loads all settings from config.env. No secrets stored here.

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env(filename: str = "config.env") -> None:
    """Parse key=value lines from config.env into os.environ (does not override)."""
    for path in (BASE_DIR / filename, BASE_DIR / ".env"):
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))
            break


_load_env()

# ── Flask server ──────────────────────────────────────────────────────────────
HOST: str = os.environ.get("KIOSK_HOST", "0.0.0.0")
PORT: int = int(os.environ.get("KIOSK_PORT", "5000"))

# ── Backend ───────────────────────────────────────────────────────────────────
BACKEND_SERVER_URL: str = os.environ.get("BACKEND_SERVER_URL", "http://127.0.0.1:8000")
AGENT_NAME: str = os.environ.get("LIVEKIT_AGENT_NAME", "sahayak-ai")

# ── Camera (OpenCV face HUD — optional) ───────────────────────────────────────
# False by default: camera stays free for Chromium's getUserMedia (document scan).
# Set ENABLE_FACE_HUD=true in config.env only when a dedicated second camera is
# available for face recognition.
ENABLE_FACE_HUD: bool = os.environ.get("ENABLE_FACE_HUD", "false").lower() == "true"
CAMERA_INDEX: int = int(os.environ.get("CAMERA_INDEX", "0"))
CAMERA_WIDTH: int = int(os.environ.get("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT: int = int(os.environ.get("CAMERA_HEIGHT", "480"))
CAMERA_FPS: int = int(os.environ.get("CAMERA_FPS", "30"))

# ── Storage paths (used by face_service when enabled) ─────────────────────────
MODELS_DIR: str = str(BASE_DIR / "models")
DB_PATH: str = str(BASE_DIR / "data" / "users.db")
