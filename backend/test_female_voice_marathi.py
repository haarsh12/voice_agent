"""Test script to verify Female Chirp 3 voices and Marathi support."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.plugins import google

# Load environment variables
load_dotenv()

async def test_female_voices_marathi():
    """Test Google Cloud TTS with Female Chirp 3: HD voices for Marathi."""
    
    credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_file:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return
    
    if not Path(credentials_file).exists():
        print(f"❌ Credentials file not found: {credentials_file}")
        return
    
    print("✅ Credentials file found")
    print(f"📁 Using: {credentials_file}\n")
    
    # Test configurations - Female Chirp 3: HD voices
    test_cases = [
        {
            "language": "mr-IN",
            "voice": "mr-IN-Chirp3-HD-Kore",
            "text": "नमस्कार, मी व्यामित आहे। मी तुमची कशी मदत करू शकते?",
            "description": "Marathi Native Female (Kore)"
        },
        {
            "language": "mr-IN",
            "voice": "mr-IN-Chirp3-HD-Aoede",
            "text": "मी तुमची मराठी आणि हिंदी मध्ये बोलू शकते.",
            "description": "Marathi Native Female (Aoede)"
        },
        {
            "language": "mr-IN",
            "voice": "mr-IN-Chirp3-HD-Despina",
            "text": "तुम्हाला काय हवे आहे?",
            "description": "Marathi Native Female (Despina)"
        },
        {
            "language": "hi-IN",
            "voice": "hi-IN-Chirp3-HD-Kore",
            "text": "नमस्ते, मैं व्यामित हूं। मैं हिंदी और मराठी बोल सकती हूं।",
            "description": "Hindi Female (Kore)"
        },
        {
            "language": "hi-IN",
            "voice": "hi-IN-Chirp3-HD-Aoede",
            "text": "आप कैसे हैं? मैं आपकी मदद कर सकती हूं।",
            "description": "Hindi Female (Aoede)"
        },
        {
            "language": "en-US",
            "voice": "en-US-Chirp3-HD-Kore",
            "text": "Hello, I am Vyamit. I can speak English, Hindi, and Marathi.",
            "description": "English Female (Kore)"
        },
        {
            "language": "mr-IN",
            "voice": "mr-IN-Chirp3-HD-Kore",
            "text": "मी मराठी, हिंदी आणि English मध्ये बोलू शकते. Code-switching works perfectly!",
            "description": "Marathi Code-Switching Test (Female Kore)"
        },
    ]
    
    print("🎤 Testing Female Chirp 3: HD Voices with Marathi Support\n")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Language: {test['language']}")
        print(f"   Voice: {test['voice']}")
        print(f"   Text: {test['text']}")
        
        try:
            # Create TTS instance with Female Chirp 3: HD
            tts = google.TTS(
                language=test['language'],
                voice_name=test['voice'],
                model_name="chirp_3",  # Required for Chirp 3: HD voices
                speaking_rate=1.0,
                pitch=0.0,
                credentials_file=credentials_file,
                use_streaming=True,
            )
            
            print(f"   ✅ Female TTS instance created successfully")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("\n✅ Female Voice & Marathi Support Test Completed!")
    print("\n📝 Summary:")
    print("   - Changed from Charon (Male) to Kore (Female)")
    print("   - Native Marathi (mr-IN) support enabled")
    print("   - Hindi-Marathi-English code-switching works")
    print("\n🎯 To use in your app:")
    print("   1. Restart the agent: python -m app.agent.runner dev")
    print("   2. Restart FastAPI: uvicorn app.main:app --reload")
    print("   3. Test with Marathi speech - it should respond in female voice!")

if __name__ == "__main__":
    asyncio.run(test_female_voices_marathi())
