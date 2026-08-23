"""Test script to verify Google Cloud TTS configuration and voice quality."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.plugins import google

# Load environment variables
load_dotenv()

async def test_google_tts():
    """Test Google Cloud TTS with Hindi, Marathi, and English voices."""
    
    credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_file:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return
    
    if not Path(credentials_file).exists():
        print(f"❌ Credentials file not found: {credentials_file}")
        return
    
    print("✅ Credentials file found")
    print(f"📁 Using: {credentials_file}\n")
    
    # Test configurations - Using Chirp 3: HD voices (required for streaming)
    test_cases = [
        {
            "language": "hi-IN",
            "voice": "hi-IN-Chirp3-HD-Charon",
            "text": "नमस्ते, मैं व्यामित हूं। मैं आपकी कैसे मदद कर सकता हूं?",
            "description": "Hindi (Female Chirp 3: HD)"
        },
        {
            "language": "hi-IN",
            "voice": "hi-IN-Chirp3-HD-Puck",
            "text": "नमस्ते, मैं व्यामित हूं। आपका दिन शुभ हो।",
            "description": "Hindi (Male Chirp 3: HD)"
        },
        {
            "language": "en-US",
            "voice": "en-US-Chirp3-HD-Charon",
            "text": "Hello, I am Vyamit. How can I help you today?",
            "description": "English (Female Chirp 3: HD)"
        },
        {
            "language": "en-US",
            "voice": "en-US-Chirp3-HD-Puck",
            "text": "Welcome to Vyamit voice assistant.",
            "description": "English (Male Chirp 3: HD)"
        },
        {
            "language": "hi-IN",
            "voice": "hi-IN-Chirp3-HD-Kore",
            "text": "नमस्कार, मी व्यामित आहे। मी तुम्हाला कशी मदत करू शकतो?",
            "description": "Marathi via Hindi Chirp 3 (code-switching)"
        },
    ]
    
    print("🎤 Testing Google Cloud TTS Voices\n")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Language: {test['language']}")
        print(f"   Voice: {test['voice']}")
        print(f"   Text: {test['text']}")
        
        try:
            # Create TTS instance with Chirp 3: HD
            tts = google.TTS(
                language=test['language'],
                voice_name=test['voice'],
                model_name="chirp_3",  # Required for Chirp 3: HD voices
                speaking_rate=1.0,
                pitch=0.0,
                credentials_file=credentials_file,
                use_streaming=True,
            )
            
            print(f"   ✅ TTS instance created successfully")
            
            # In a real scenario, you would synthesize and play audio
            # For this test, we just verify the instance can be created
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("\n✅ Google Cloud TTS test completed!")
    print("\nNote: This test verifies TTS initialization.")
    print("To hear actual audio, run the full agent with:")
    print("  python -m app.agent.runner dev")

if __name__ == "__main__":
    asyncio.run(test_google_tts())
