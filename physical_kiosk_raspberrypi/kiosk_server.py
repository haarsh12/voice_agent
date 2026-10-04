# Sahayak AI — Raspberry Pi Physical Kiosk Server
# Hardware API Gateway + Chromium UI Backend + Backend Proxy
#
# Responsibilities:
#   • Serves the full-featured Chromium touch UI (templates/index.html)
#   • Proxies all backend API calls with X-Sahayak-Device: raspberrypi header
#   • Manages hardware: microphone (ALSA VAD/PTT), speaker (TTS), camera (MJPEG/Face)
#   • Provides Server-Sent Events stream for volume/transcript UI updates

import os
import sys
import time
import json
import queue
import logging
import subprocess
import requests
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request, stream_with_context

import config
from stt_service import STTService
from audio_capture import HybridAudioCapturer
from face_service import FaceService, CameraStreamThread

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SahayakKioskServer")

# ──────────────────────────────────────────────
# Flask App
# ──────────────────────────────────────────────
app = Flask(__name__)

# Queue for SSE events to the Chromium UI (volume, transcripts)
event_queue: queue.Queue = queue.Queue(maxsize=200)

# Header identifying this device to the backend
DEVICE_HEADER = {"X-Sahayak-Device": "raspberrypi"}

# ──────────────────────────────────────────────
# Hardware Service Instances
# ──────────────────────────────────────────────
stt_engine = STTService(sample_rate=config.TARGET_SAMPLE_RATE)
face_service = FaceService(models_dir=config.MODELS_DIR, db_path=config.DB_PATH)
camera_thread = CameraStreamThread(camera_id=config.CAMERA_INDEX, face_service=face_service)


# ──────────────────────────────────────────────
# Guest Session Cache (for STT/text-chat fallback)
# ──────────────────────────────────────────────
_guest_session: dict | None = None


def get_or_create_backend_guest_session() -> dict | None:
    """Returns or creates a guest session with the central backend."""
    global _guest_session
    if _guest_session:
        return _guest_session

    backend_url = config.BACKEND_SERVER_URL.rstrip("/")
    try:
        logger.info(f"Creating kiosk guest session at {backend_url}/api/guest-sessions")
        res = requests.post(
            f"{backend_url}/api/guest-sessions",
            headers=DEVICE_HEADER,
            timeout=8,
        )
        if res.status_code in (200, 201):
            _guest_session = res.json()
            logger.info(f"Guest session created: {_guest_session.get('session_id')}")
            return _guest_session
        logger.warning(f"Guest session error ({res.status_code}): {res.text[:200]}")
    except Exception as exc:
        logger.warning(f"Cannot reach backend for guest session: {exc}")
    return None


# ──────────────────────────────────────────────
# Voice Query Pipeline (STT-based, hardware mic)
# ──────────────────────────────────────────────
def _push_event(payload: dict) -> None:
    """Non-blocking push to SSE event queue."""
    try:
        event_queue.put_nowait(payload)
    except queue.Full:
        pass


def send_transcript_to_backend(text: str) -> str | None:
    """Forward a transcribed utterance to the backend /api/chat endpoint."""
    if not text or text.startswith("["):
        return None

    session = get_or_create_backend_guest_session()
    backend_url = config.BACKEND_SERVER_URL.rstrip("/")

    form_data: dict = {
        "message": text,
        "language": config.STT_LANGUAGE,
    }
    if session:
        form_data["guest_session_id"] = session.get("session_id", "")
        form_data["guest_session_secret"] = session.get("session_secret", "")

    try:
        logger.info(f"Forwarding STT query to backend: {text!r}")
        res = requests.post(
            f"{backend_url}/api/chat",
            data=form_data,
            headers=DEVICE_HEADER,
            timeout=15,
        )
        if res.status_code == 200:
            data = res.json()
            return data.get("message") or data.get("response") or data.get("reply") or data.get("text")
        logger.warning(f"Backend chat returned {res.status_code}: {res.text[:200]}")
    except Exception as exc:
        logger.warning(f"Backend chat unreachable: {exc}")
    return None


def speak_text(text: str) -> None:
    """Synthesize speech via espeak-ng and play through ALSA speaker."""
    if not text or text.startswith("["):
        return
    logger.info(f"🔊 TTS → '{text[:80]}'")
    try:
        wav_path = "/tmp/sahayak_tts.wav"
        result = subprocess.run(
            ["espeak-ng", "-v", "en-us", "-a", "200", "-s", "140", "-w", wav_path, text],
            capture_output=True, timeout=8,
        )
        if result.returncode == 0 and os.path.exists(wav_path):
            play = subprocess.run(
                ["aplay", "-D", config.ALSA_PLAYBACK_DEVICE, wav_path],
                capture_output=True, timeout=12,
            )
            if play.returncode != 0:
                # Fallback to Google voice card default
                subprocess.run(
                    ["aplay", "-D", "plughw:CARD=sndrpigooglevoi,DEV=0", wav_path],
                    capture_output=True, timeout=12,
                )
    except Exception as exc:
        logger.warning(f"TTS playback error: {exc}")


def process_voice_query(transcript: str, timestamp_str: str) -> None:
    """Handle a recognized mic utterance: push to UI, query backend, speak reply."""
    if not transcript or transcript.startswith("["):
        return

    _push_event({"type": "transcript", "sender": "user", "timestamp": timestamp_str, "text": transcript})

    ai_reply = send_transcript_to_backend(transcript)
    if not ai_reply:
        ai_reply = f"Recognized: '{transcript}'. Connecting to Sahayak AI."

    _push_event({
        "type": "transcript",
        "sender": "assistant",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "text": ai_reply,
    })
    speak_text(ai_reply)


def on_auto_speech_captured(pcm16_bytes: bytes, volume: float) -> None:
    """VAD callback: transcribe auto-detected speech and process the query."""
    if not pcm16_bytes:
        return
    logger.info("Auto VAD: transcribing captured mic audio...")
    transcript = stt_engine.transcribe_pcm16_chunk(pcm16_bytes)
    if transcript:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'='*55}\n 🎙️  [{ts}] AUTO VAD: \"{transcript}\"\n{'='*55}\n", flush=True)
        process_voice_query(transcript, ts)


# ──────────────────────────────────────────────
# Audio Capturer
# ──────────────────────────────────────────────
audio_capturer = HybridAudioCapturer(
    callback=on_auto_speech_captured,
    alsa_device=config.ALSA_RECORD_DEVICE,
    sample_rate=config.SAMPLE_RATE,
    channels=config.CHANNELS,
    bit_depth=config.BIT_DEPTH,
)


# ══════════════════════════════════════════════
# Flask Routes — UI
# ══════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the Chromium kiosk SPA."""
    return render_template(
        "index.html",
        backend_url=config.BACKEND_SERVER_URL,
        alsa_device=config.ALSA_RECORD_DEVICE,
    )


# ══════════════════════════════════════════════
# Flask Routes — Backend API Proxy
# All calls add X-Sahayak-Device: raspberrypi and forward to the backend.
# The Chromium UI calls these /api/kiosk/* endpoints instead of the backend
# directly so that no backend URL or credentials ever appear in the page.
# ══════════════════════════════════════════════

def _backend(path: str) -> str:
    return f"{config.BACKEND_SERVER_URL.rstrip('/')}{path}"


def _proxy_headers(extra: dict | None = None) -> dict:
    """Build forwarded headers: merge device header + any caller extras."""
    hdrs = dict(DEVICE_HEADER)
    # Forward cookies from the Chromium request so authenticated sessions work
    if request.cookies:
        hdrs["Cookie"] = "; ".join(f"{k}={v}" for k, v in request.cookies.items())
    if extra:
        hdrs.update(extra)
    return hdrs


@app.route("/api/kiosk/config")
def kiosk_config():
    """Return kiosk-specific configuration for the Chromium UI."""
    return jsonify({
        "agent_name": config.AGENT_NAME,
        "default_language": config.STT_LANGUAGE,
        "backend_url": config.BACKEND_SERVER_URL,  # NOT exposed to UI directly; included for debug
    })


@app.route("/api/kiosk/token")
def kiosk_token():
    """
    Proxy the LiveKit token endpoint to the backend with the raspberrypi
    device identifier added.  The UI calls this instead of the backend
    directly so the backend URL never appears in the browser source.
    """
    # Forward all query params from the Chromium page
    params = dict(request.args)
    params["client_device"] = "raspberrypi"  # ensure correct device flag

    try:
        res = requests.get(
            _backend("/api/token"),
            params=params,
            headers=_proxy_headers(),
            timeout=10,
        )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.error(f"Token proxy error: {exc}")
        return jsonify({"detail": "LiveKit token service unreachable"}), 503


@app.route("/api/kiosk/guest-session", methods=["POST"])
def kiosk_guest_session():
    """Proxy guest session creation to the backend with raspberrypi device header."""
    try:
        res = requests.post(
            _backend("/api/guest-sessions"),
            headers=_proxy_headers(),
            timeout=8,
        )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.error(f"Guest session proxy error: {exc}")
        return jsonify({"detail": "Backend guest session service unreachable"}), 503


@app.route("/api/kiosk/chat", methods=["POST"])
def kiosk_chat():
    """
    Proxy text-chat (and document upload) to the backend /api/chat endpoint.
    Accepts multipart/form-data from the Chromium UI.
    """
    try:
        files = {}
        if "document" in request.files:
            f = request.files["document"]
            files["document"] = (f.filename, f.stream, f.content_type)

        res = requests.post(
            _backend("/api/chat"),
            data=request.form.to_dict(),
            files=files if files else None,
            headers=_proxy_headers(),
            timeout=30,
        )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.error(f"Chat proxy error: {exc}")
        return jsonify({"detail": "Backend chat service unreachable"}), 503


@app.route("/api/kiosk/health")
def kiosk_health_proxy():
    """Proxy backend health check."""
    try:
        res = requests.get(_backend("/api/health"), headers=_proxy_headers(), timeout=5)
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.warning(f"Health proxy error: {exc}")
        return jsonify({"configured": False, "error": str(exc)}), 503


@app.route("/api/kiosk/schemes")
def kiosk_schemes_proxy():
    """Proxy scheme search to the backend."""
    try:
        res = requests.get(
            _backend("/api/schemes"),
            params=request.args,
            headers=_proxy_headers(),
            timeout=12,
        )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.error(f"Schemes proxy error: {exc}")
        return jsonify({"detail": "Schemes service unreachable"}), 503


@app.route("/api/kiosk/grievances", methods=["GET", "POST"])
def kiosk_grievances_proxy():
    """Proxy grievance list/create to the backend."""
    try:
        if request.method == "GET":
            res = requests.get(
                _backend("/api/grievances"),
                params=request.args,
                headers=_proxy_headers(),
                timeout=10,
            )
        else:
            res = requests.post(
                _backend("/api/grievances"),
                json=request.get_json(silent=True),
                headers=_proxy_headers({"Content-Type": "application/json"}),
                timeout=15,
            )
        return Response(
            res.content,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json"),
        )
    except Exception as exc:
        logger.error(f"Grievances proxy error: {exc}")
        return jsonify({"detail": "Grievances service unreachable"}), 503


# ══════════════════════════════════════════════
# Flask Routes — Hardware APIs
# ══════════════════════════════════════════════

@app.route("/api/hardware_status")
def hardware_status():
    """Returns hardware + backend connectivity status for the UI status bar."""
    backend_online = False
    try:
        res = requests.get(_backend("/api/health"), headers=DEVICE_HEADER, timeout=3)
        backend_online = res.status_code == 200
    except Exception:
        pass

    return jsonify({
        "status": "online",
        "device": "raspberrypi",
        "backend_url": config.BACKEND_SERVER_URL,
        "backend_connected": backend_online,
        "mic": config.ALSA_RECORD_DEVICE,
        "speaker": config.ALSA_PLAYBACK_DEVICE,
        "camera_active": camera_thread.is_running,
        "audio_capturer_active": audio_capturer.is_running,
    })


@app.route("/start_recording", methods=["POST"])
def start_recording():
    """Start push-to-talk recording on the hardware mic."""
    audio_capturer.start_button_recording()
    return jsonify({"status": "recording_started", "message": "Listening..."})


@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    """Stop push-to-talk recording, transcribe, and forward to backend."""
    pcm16_bytes = audio_capturer.stop_button_recording()

    if not pcm16_bytes:
        return jsonify({"status": "empty", "transcript": "[No speech recorded]"})

    logger.info(f"Transcribing {len(pcm16_bytes)} bytes of push-to-talk audio...")
    transcript = stt_engine.transcribe_pcm16_chunk(pcm16_bytes)
    ts = datetime.now().strftime("%H:%M:%S")

    if not transcript:
        transcript = "[Could not recognize speech]"

    print(f"\n{'='*55}\n 🎙️  [{ts}] PTT: \"{transcript}\"\n{'='*55}\n", flush=True)

    if not transcript.startswith("["):
        process_voice_query(transcript, ts)

    return jsonify({"status": "success", "timestamp": ts, "transcript": transcript})


@app.route("/stream")
def stream():
    """SSE stream: volume meter updates and transcript events to Chromium UI."""
    def event_generator():
        last_vol_time = 0.0
        while True:
            # Drain queued events first
            try:
                data = event_queue.get(timeout=0.15)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                pass

            # Throttled volume update
            now = time.time()
            if now - last_vol_time >= 0.15:
                last_vol_time = now
                yield f"data: {json.dumps({'type': 'volume', 'level': audio_capturer.current_volume, 'is_recording': audio_capturer.is_button_recording})}\n\n"

    return Response(
        stream_with_context(event_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/video_feed")
def video_feed():
    """MJPEG camera stream (used for face HUD display, not document capture)."""
    def generate_frames():
        while True:
            frame_bytes = camera_thread.get_mjpeg_frame()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
            time.sleep(0.033)  # ~30 fps

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ══════════════════════════════════════════════
# Main Entry Point
# ══════════════════════════════════════════════

def main() -> None:
    logger.info("=" * 60)
    logger.info(" Sahayak AI — Raspberry Pi Physical Kiosk Server")
    logger.info("=" * 60)
    logger.info(f"  Backend URL   : {config.BACKEND_SERVER_URL}")
    logger.info(f"  Agent Name    : {config.AGENT_NAME}")
    logger.info(f"  Record Device : {config.ALSA_RECORD_DEVICE}")
    logger.info(f"  Playback Dev  : {config.ALSA_PLAYBACK_DEVICE}")
    logger.info(f"  Kiosk Port    : {config.PORT}")
    logger.info("=" * 60)

    # Warm up guest session
    get_or_create_backend_guest_session()

    # Start hardware subsystems
    audio_capturer.start()
    camera_thread.start()

    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except KeyboardInterrupt:
        logger.info("Kiosk server shutting down...")
    finally:
        audio_capturer.stop()
        camera_thread.stop()
        logger.info("Hardware stopped. Goodbye.")


if __name__ == "__main__":
    main()
