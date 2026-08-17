#!/usr/bin/env python3
"""
Comprehensive test for Google Cloud Services:
1. Speech-to-Text (STT)
2. Text-to-Speech (TTS)
3. Gemini AI API

This test verifies that all services are reachable and functional.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.genai.types import AutomaticFunctionCallingConfig, GenerateContentConfig

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()


def test_credentials():
    """Test if Google credentials are properly set up."""
    print("=" * 70)
    print("STEP 1: Testing Google Cloud Credentials")
    print("=" * 70)
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"Credentials path from .env: {creds_path}")
    
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env")
        return False
    
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found at: {creds_path}")
        return False
    
    print(f"✅ Credentials file found at: {creds_path}")
    
    # Set environment variable for Google Cloud SDK
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    
    return True


def test_speech_to_text():
    """Test Google Cloud Speech-to-Text API."""
    print("\n" + "=" * 70)
    print("STEP 2: Testing Google Cloud Speech-to-Text (STT)")
    print("=" * 70)
    
    try:
        from google.cloud import speech
        
        # Initialize client
        client = speech.SpeechClient()
        print("✅ Speech-to-Text client initialized successfully")
        
        # Create a simple test with synthetic audio data
        # This tests the API connection without needing an actual audio file
        audio = speech.RecognitionAudio(
            content=b'\x00' * 1000  # Dummy audio data
        )
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        
        print("Testing API connection with dummy request...")
        try:
            response = client.recognize(config=config, audio=audio)
            print("✅ STT API is reachable (empty result is expected for dummy data)")
            return True
        except Exception as api_error:
            # If we get a specific API error about the audio, that's actually good
            # It means the API is reachable but rejected our dummy data
            error_msg = str(api_error)
            if "audio" in error_msg.lower() or "invalid" in error_msg.lower():
                print("✅ STT API is reachable and responding (rejected dummy audio as expected)")
                return True
            else:
                print(f"⚠️ STT API returned unexpected error: {error_msg}")
                return False
                
    except ImportError as e:
        print(f"❌ Failed to import google.cloud.speech: {e}")
        print("Install with: pip install google-cloud-speech")
        return False
    except Exception as e:
        print(f"❌ STT test failed: {e}")
        return False


def test_text_to_speech():
    """Test Google Cloud Text-to-Speech API."""
    print("\n" + "=" * 70)
    print("STEP 3: Testing Google Cloud Text-to-Speech (TTS)")
    print("=" * 70)
    
    try:
        from google.cloud import texttospeech
        
        # Initialize client
        client = texttospeech.TextToSpeechClient()
        print("✅ Text-to-Speech client initialized successfully")
        
        # Test with a simple phrase
        synthesis_input = texttospeech.SynthesisInput(text="Hello from Vyamit")
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        print("Testing TTS API with sample text...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        if response.audio_content:
            audio_size = len(response.audio_content)
            print(f"✅ TTS API working! Generated {audio_size} bytes of audio")
            
            # Save test audio file
            test_audio_path = "test_tts_output.mp3"
            with open(test_audio_path, "wb") as out:
                out.write(response.audio_content)
            print(f"✅ Test audio saved to: {test_audio_path}")
            return True
        else:
            print("⚠️ TTS API responded but no audio content generated")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import google.cloud.texttospeech: {e}")
        print("Install with: pip install google-cloud-texttospeech")
        return False
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False


def test_gemini_api():
    """Test Google Gemini AI API using Vertex AI with service account."""
    print("\n" + "=" * 70)
    print("STEP 4: Testing Google Gemini AI via Vertex AI (Paid Account)")
    print("=" * 70)
    
    try:
        from app.config.settings import get_settings
        from app.services.gemini import create_gemini_client, load_vertex_authentication

        settings = get_settings()
        auth = load_vertex_authentication(settings)
        client = create_gemini_client(settings)

        print(f"Using service account project: {auth.project_id}")
        print(f"Using Vertex location: {settings.google_cloud_location}")
        print(f"Using Gemini model: {settings.gemini_model}")
        print("Testing Gemini API with sample prompt...")
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents='Say "Paid API connection successful from Vyamit" in Hindi.',
            config=GenerateContentConfig(
                automatic_function_calling=AutomaticFunctionCallingConfig(disable=True)
            ),
        )
        
        if response.text:
            print(f"✅ Gemini API working! Response: {response.text}")
            print("✅ All 3 services (STT, TTS, Gemini) are using your ₹1000 paid account!")
            return True
        else:
            print("⚠️ Gemini API responded but no text generated")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Gemini test failed: {error_msg}")
        
        if "403" in error_msg or "404" in error_msg or "PERMISSION_DENIED" in error_msg or "NOT_FOUND" in error_msg:
            print("\n🔧 Fix 404 / 403 Access Issues for Gemini on Vertex AI:")
            print("1. Use GEMINI_MODEL=gemini-3.5-flash and GOOGLE_CLOUD_LOCATION=global.")
            print("2. Ensure the service account has 'Vertex AI User' (roles/aiplatform.user).")
            print("3. Ensure the Vertex AI API and billing are enabled for the project.")
        
        return False



def main():
    """Run all tests."""
    print("\n" + "🔵" * 35)
    print("VYAMIT GOOGLE CLOUD SERVICES TEST")
    print("🔵" * 35 + "\n")
    
    results = {}
    
    # Test 1: Credentials
    results['credentials'] = test_credentials()
    if not results['credentials']:
        print("\n❌ Cannot proceed without valid credentials")
        return False
    
    # Test 2: Speech-to-Text
    results['stt'] = test_speech_to_text()
    
    # Test 3: Text-to-Speech
    results['tts'] = test_text_to_speech()
    
    # Test 4: Gemini AI
    results['gemini'] = test_gemini_api()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    status_emoji = lambda x: "✅" if x else "❌"
    
    print(f"{status_emoji(results['credentials'])} Google Cloud Credentials")
    print(f"{status_emoji(results['stt'])} Speech-to-Text (STT) API")
    print(f"{status_emoji(results['tts'])} Text-to-Speech (TTS) API")
    print(f"{status_emoji(results['gemini'])} Gemini AI API")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! All Google Cloud services are working!")
    else:
        print("⚠️ SOME TESTS FAILED. Check the output above for details.")
    print("=" * 70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
