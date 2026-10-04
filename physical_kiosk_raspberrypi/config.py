# Sahayak AI - Raspberry Pi Kiosk & Hardware Controller
# Production Configuration Settings

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_env_file(env_filename="config.env"):
    """
    Parses key=value pairs from env file into os.environ.
    """
    env_path = BASE_DIR / env_filename
    if not env_path.exists():
        env_path = BASE_DIR / ".env"

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip().strip("'\"")
                    os.environ[key] = val

load_env_file()

# Google Cloud Application Credentials Validation
g_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if g_creds and not os.path.isabs(g_creds):
    abs_creds = str(BASE_DIR / g_creds)
    if os.path.exists(abs_creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_creds

# Server / Backend Configuration
HOST = os.environ.get("KIOSK_HOST", "0.0.0.0")
PORT = int(os.environ.get("KIOSK_PORT", 5000))
BACKEND_SERVER_URL = os.environ.get("BACKEND_SERVER_URL", "http://127.0.0.1:5000")

# ALSA Audio Device Settings (Supports both USB Mic & INMP441 I2S MEMS Mic)
ALSA_RECORD_DEVICE = os.environ.get("ALSA_RECORD_DEVICE", "plughw:CARD=sndrpigooglevoi,DEV=0")
ALSA_PLAYBACK_DEVICE = os.environ.get("ALSA_PLAYBACK_DEVICE", "plughw:CARD=sndrpigooglevoi,DEV=0")
SAMPLE_RATE = int(os.environ.get("AUDIO_SAMPLE_RATE", 48000))
CHANNELS = int(os.environ.get("AUDIO_CHANNELS", 2))
BIT_DEPTH = os.environ.get("AUDIO_BIT_DEPTH", "S32_LE")
TARGET_SAMPLE_RATE = 16000

# Camera Hardware Settings
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", 0))
CAMERA_WIDTH = int(os.environ.get("CAMERA_WIDTH", 640))
CAMERA_HEIGHT = int(os.environ.get("CAMERA_HEIGHT", 480))
CAMERA_FPS = int(os.environ.get("CAMERA_FPS", 30))

# SQLite Database & Model Paths
MODELS_DIR = str(BASE_DIR / "models")
DB_PATH = str(BASE_DIR / "data" / "users.db")
