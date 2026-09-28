#!/usr/bin/env python3
"""
Complete verification test for Google Cloud Services:
- Gemini AI (via Vertex AI)
- Speech-to-Text (STT)
- Text-to-Speech (TTS)

Uses service account credentials from your ₹1000 paid Google Cloud account.
"""

import os
import sys
import time
from dotenv import load_dotenv
from google.genai.types import AutomaticFunctionCallingConfig, GenerateContentConfig

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


print("=" * 80)
print("         VYAMIT GOOGLE CLOUD ENTERPRISE SERVICES TEST")
print("=" * 80 + "\n")

# Load environment variables
load_dotenv()

# ======================================================================
# STEP 1: Verify Credentials
# ======================================================================
print("--- STEP 1: Validating Credentials ---")
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not creds_path:
    print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not found in .env")
    exit(1)

if not os.path.exists(creds_path):
    print(f"❌ ERROR: File not found at: {creds_path}")
    exit(1)

print(f"✅ Credentials file found: {creds_path}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

print("🔄 Initializing Google Cloud clients...\n")

try:
    from google.cloud import speech
    from google.cloud import texttospeech
    from app.config.settings import get_settings
    from app.services.gemini import create_gemini_client, load_vertex_authentication

    settings = get_settings()
    vertex_auth = load_vertex_authentication(settings)
    gemini_client = create_gemini_client(settings)

    # Initialize clients
    stt_client = speech.SpeechClient()
    tts_client = texttospeech.TextToSpeechClient()
    
    print(f"✅ All client libraries initialized for {vertex_auth.project_id}!\n")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Install: pip install google-genai google-cloud-speech google-cloud-texttospeech python-dotenv")
    exit(1)

# ======================================================================
# STEP 2: Test Gemini via Vertex AI
# ======================================================================
print("--- STEP 2: Testing Gemini AI (Vertex AI) ---")
print("🔄 Sending request to Gemini model...")

try:
    start_time = time.time()
    response = gemini_client.models.generate_content(
        model=settings.gemini_model,
        contents='Say "Paid Enterprise Cloud connection successful from Vyamit!" in Hindi.',
        config=GenerateContentConfig(
            automatic_function_calling=AutomaticFunctionCallingConfig(disable=True)
        ),
    )
    latency = time.time() - start_time
    
    print(f"✅ Gemini Response Received ({latency:.2f}s)!")
    print(f"🤖 Gemini Output: {response.text.strip()}\n")
    
except Exception as e:
    print(f"❌ Gemini Failed: {e}\n")

# ======================================================================
# STEP 3: Test Text-to-Speech
# ======================================================================
print("--- STEP 3: Testing Text-to-Speech (TTS) ---")
print("🔄 Generating audio from text...")

try:
    start_time = time.time()
    
    synthesis_input = texttospeech.SynthesisInput(
        text="Google Cloud services are working perfectly with your paid account."
    )
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    tts_response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    latency = time.time() - start_time
    
    output_file = "test_tts_verification.mp3"
    with open(output_file, "wb") as out:
        out.write(tts_response.audio_content)
    
    print(f"✅ TTS Generated {len(tts_response.audio_content)} bytes ({latency:.2f}s)!")
    print(f"🎵 Audio saved to: {output_file}\n")
    
except Exception as e:
    print(f"❌ TTS Failed: {e}\n")

# ======================================================================
# STEP 4: Test Speech-to-Text
# ======================================================================
print("--- STEP 4: Testing Speech-to-Text (STT) ---")
print("🔄 Verifying STT API connectivity...")

try:
    start_time = time.time()
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    
    # Dummy audio to test connection
    audio = speech.RecognitionAudio(content=b'\x00' * 32000)
    
    stt_client.recognize(config=config, audio=audio)
    latency = time.time() - start_time
    
    print(f"✅ STT API reachable ({latency:.2f}s)!")
    print("📢 Ready to stream microphone audio.\n")
    
except Exception as e:
    print(f"❌ STT Failed: {e}\n")

print("=" * 80)
print("                      TEST COMPLETE")
print("  All 3 services (Gemini, STT, TTS) using your ₹1000 paid account!")
print("=" * 80)
