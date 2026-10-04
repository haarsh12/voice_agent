# Production Kiosk Server and Hardware API Gateway
# Orchestrates Mic, Speaker, Camera, Touch Screen REST API and SSE Event Stream

import os
import sys
import time
import json
import queue
import logging
import subprocess
import requests
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request

import config
from stt_service import STTService
from audio_capture import HybridAudioCapturer
from face_service import FaceService, CameraStreamThread

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SahayakKioskServer")

app = Flask(__name__)

# Queue for Touch Screen Web UI real-time events
event_queue = queue.Queue(maxsize=100)

# Active guest session tracking for backend API calls
guest_session = None

# Hardware Service Instances
stt_engine = STTService(sample_rate=config.TARGET_SAMPLE_RATE)
face_service = FaceService(models_dir=config.MODELS_DIR, db_path=config.DB_PATH)
camera_thread = CameraStreamThread(camera_id=config.CAMERA_INDEX, face_service=face_service)

def get_or_create_backend_guest_session():
    """
    Ensures an active guest session exists with the central backend server API.
    """
    global guest_session
    if guest_session:
        return guest_session

    backend_url = config.BACKEND_SERVER_URL.rstrip('/')
    session_endpoint = f"{backend_url}/api/guest-sessions"
    try:
        logger.info(f"Creating new guest session at backend: {session_endpoint}")
        res = requests.post(session_endpoint, timeout=5)
        if res.status_code in (200, 201):
            guest_session = res.json()
            logger.info(f"Connected guest session: {guest_session.get('session_id')}")
            return guest_session
        else:
            logger.warning(f"Failed to create guest session ({res.status_code}): {res.text}")
    except Exception as e:
        logger.warning(f"Backend guest session request failed: {e}")
    return None

def send_transcript_to_backend(text: str):
    """
    Sends transcribed voice input to central backend /api/chat endpoint
    and synthesizes backend response via speaker.
    """
    if not text or text.startswith("["):
        return None

    session = get_or_create_backend_guest_session()
    backend_url = config.BACKEND_SERVER_URL.rstrip('/')
    chat_endpoint = f"{backend_url}/api/chat"

    payload = {
        "message": text,
        "language": "hi-IN"
    }

    if session:
        payload["guest_session_id"] = session.get("session_id")
        payload["guest_session_secret"] = session.get("session_secret")

    try:
        logger.info(f"Forwarding query to backend AI endpoint '{chat_endpoint}': {text}")
        res = requests.post(chat_endpoint, data=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            ai_reply = data.get("response") or data.get("reply") or data.get("text")
            if ai_reply:
                logger.info(f"🤖 Backend AI Response: '{ai_reply}'")
                return ai_reply
        else:
            logger.warning(f"Backend API returned status {res.status_code}: {res.text}")
    except Exception as e:
        logger.warning(f"Could not connect to central backend chat API: {e}")

    return None

def speak_text(text: str):
    """
    Synthesizes and plays back speech via ALSA speaker output using espeak-ng and aplay.
    """
    if not text or text.startswith("["):
        return
    playback_dev = config.ALSA_PLAYBACK_DEVICE
    logger.info(f"🔊 Playing Audio Output on '{playback_dev}': '{text}'")
    try:
        wav_path = "/tmp/tts_out.wav"
        res = subprocess.run(["espeak-ng", "-v", "en-us", "-a", "200", "-s", "140", "-w", wav_path, text], capture_output=True, timeout=5)
        if res.returncode == 0 and os.path.exists(wav_path):
            play_res = subprocess.run(["aplay", "-D", playback_dev, wav_path], capture_output=True, timeout=10)
            if play_res.returncode != 0 and playback_dev != "plughw:CARD=sndrpigooglevoi,DEV=0":
                logger.info("Retrying aplay with default ALSA fallback device...")
                play_res = subprocess.run(["aplay", "-D", "plughw:CARD=sndrpigooglevoi,DEV=0", wav_path], capture_output=True, timeout=10)
            if play_res.returncode != 0:
                logger.warning(f"aplay warning ({play_res.returncode}): {play_res.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        logger.warning(f"Could not synthesize/play TTS output: {e}")

def process_voice_query(transcript: str, timestamp_str: str):
    """
    Handles recognized transcript: forwards to backend, updates UI, and speaks AI reply.
    """
    if not transcript or transcript.startswith("["):
        return

    # Broadcast User Transcript to Web UI
    user_payload = {
        "type": "transcript",
        "sender": "user",
        "timestamp": timestamp_str,
        "text": transcript
    }
    try:
        event_queue.put_nowait(user_payload)
    except queue.Full:
        pass

    # Send to Central Backend Server API
    ai_reply = send_transcript_to_backend(transcript)

    # Fallback response if offline/unreachable
    if not ai_reply:
        ai_reply = f"Recognized query: '{transcript}'. Connecting to Sahayak AI backend."

    # Broadcast AI Response to Web UI
    ai_payload = {
        "type": "transcript",
        "sender": "assistant",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "text": ai_reply
    }
    try:
        event_queue.put_nowait(ai_payload)
    except queue.Full:
        pass

    # Speak response out of Raspberry Pi Speakers
    speak_text(ai_reply)

def on_auto_speech_captured(pcm16_bytes: bytes, volume: float):
    """
    Invoked when speech is automatically detected by Mic VAD.
    """
    if not pcm16_bytes or len(pcm16_bytes) == 0:
        return

    logger.info("Processing auto-captured mic audio clip with Google STT...")
    transcript = stt_engine.transcribe_pcm16_chunk(pcm16_bytes)
    if transcript:
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        
        print("\n=======================================================")
        print(f" 🎙️  [AUTO VOICE TRANSCRIPTION | {timestamp_str}]")
        print(f"     \"{transcript}\"")
        print("=======================================================\n", flush=True)

        process_voice_query(transcript, timestamp_str)

# Audio Capturer Instance
audio_capturer = HybridAudioCapturer(
    callback=on_auto_speech_captured,
    alsa_device=config.ALSA_RECORD_DEVICE,
    sample_rate=config.SAMPLE_RATE,
    channels=config.CHANNELS,
    bit_depth=config.BIT_DEPTH
)

@app.route("/")
def index():
    return render_template("index.html", backend_url=config.BACKEND_SERVER_URL, alsa_device=config.ALSA_RECORD_DEVICE)

@app.route("/api/hardware_status")
def hardware_status():
    backend_online = False
    try:
        res = requests.get(f"{config.BACKEND_SERVER_URL.rstrip('/')}/api/health", timeout=3)
        backend_online = (res.status_code == 200)
    except Exception:
        pass

    return jsonify({
        "status": "online",
        "backend_url": config.BACKEND_SERVER_URL,
        "backend_connected": backend_online,
        "mic": config.ALSA_RECORD_DEVICE,
        "speaker": config.ALSA_PLAYBACK_DEVICE,
        "camera_active": camera_thread.is_running,
        "audio_capturer_active": audio_capturer.is_running
    })

@app.route("/start_recording", methods=["POST"])
def start_recording():
    audio_capturer.start_button_recording()
    return jsonify({"status": "recording_started", "message": "Listening..."})

@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    pcm16_bytes = audio_capturer.stop_button_recording()
    
    if not pcm16_bytes or len(pcm16_bytes) == 0:
        return jsonify({"status": "empty", "transcript": "[No speech recorded]"})

    logger.info(f"Transcribing {len(pcm16_bytes)} bytes of recorded button speech...")
    transcript = stt_engine.transcribe_pcm16_chunk(pcm16_bytes)
    timestamp_str = datetime.now().strftime("%H:%M:%S")

    if not transcript:
        transcript = "[Could not recognize speech]"

    print("\n=======================================================")
    print(f" 🎙️  [BUTTON SPEECH TRANSCRIPTION | {timestamp_str}]")
    print(f"     \"{transcript}\"")
    print("=======================================================\n", flush=True)

    if not transcript.startswith("["):
        process_voice_query(transcript, timestamp_str)

    return jsonify({"status": "success", "timestamp": timestamp_str, "transcript": transcript})

@app.route("/stream")
def stream():
    def event_generator():
        last_vol_time = 0
        while True:
            try:
                data = event_queue.get(timeout=0.2)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                pass

            now = time.time()
            if now - last_vol_time >= 0.15:
                last_vol_time = now
                vol_payload = {
                    "type": "volume",
                    "level": audio_capturer.current_volume,
                    "is_recording": audio_capturer.is_button_recording
                }
                yield f"data: {json.dumps(vol_payload)}\n\n"

    return Response(event_generator(), mimetype="text/event-stream")

@app.route("/video_feed")
def video_feed():
    def generate_frames():
        while True:
            frame_bytes = camera_thread.get_mjpeg_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    logger.info("Starting Sahayak AI Raspberry Pi Kiosk Server...")
    logger.info(f"Backend Server URL: {config.BACKEND_SERVER_URL}")
    logger.info(f"Record Device: {config.ALSA_RECORD_DEVICE}")
    logger.info(f"Playback Device: {config.ALSA_PLAYBACK_DEVICE}")

    # Initialize backend guest session on startup
    get_or_create_backend_guest_session()

    audio_capturer.start()
    camera_thread.start()

    try:
        app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Shutting down kiosk server...")
    finally:
        audio_capturer.stop()
        camera_thread.stop()

if __name__ == "__main__":
    main()
