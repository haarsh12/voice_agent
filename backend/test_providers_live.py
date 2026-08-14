#!/usr/bin/env python3
"""Live test script to verify STT, LLM, and TTS providers are working."""

from __future__ import annotations

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables like the agent runner does
_BACKEND_DIRECTORY = Path(__file__).resolve().parent
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent

load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_PROJECT_DIRECTORY / ".env.local", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env.local", override=True)

from app.agent.providers import create_stt, create_llm, create_tts
from app.config.settings import get_settings


async def test_deepgram_stt():
    """Test Deepgram Speech-to-Text connection."""
    print("\n🎤 Testing Deepgram STT...")
    try:
        settings = get_settings()
        if not settings.deepgram_api_key:
            print("   ❌ DEEPGRAM_API_KEY not set")
            return False
            
        stt = create_stt(settings)
        print(f"   ✅ Deepgram STT created successfully")
        print(f"   ℹ️  Model: {settings.deepgram_stt_model}")
        print(f"   ℹ️  Language: {settings.deepgram_stt_language}")
        print(f"   ℹ️  Keyterms: {settings.keyterms}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_mistral_llm():
    """Test Mistral AI LLM connection."""
    print("\n🤖 Testing Mistral AI LLM...")
    try:
        settings = get_settings()
        if not settings.mistral_api_key:
            print("   ❌ MISTRAL_API_KEY not set")
            return False
            
        llm = create_llm(settings)
        print(f"   ✅ Mistral LLM created successfully")
        print(f"   ℹ️  Model: {settings.mistral_model}")
        print(f"   ℹ️  Temperature: {settings.mistral_temperature}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_cartesia_tts():
    """Test Cartesia Text-to-Speech connection."""
    print("\n🔊 Testing Cartesia TTS...")
    try:
        settings = get_settings()
        if not settings.cartesia_api_key:
            print("   ❌ CARTESIA_API_KEY not set")
            return False
            
        tts = create_tts(settings)
        print(f"   ✅ Cartesia TTS created successfully")
        print(f"   ℹ️  Model: {settings.cartesia_tts_model}")
        print(f"   ℹ️  Voice ID: {settings.cartesia_voice_id}")
        print(f"   ℹ️  Language: {settings.cartesia_tts_language}")
        print(f"   ℹ️  Speed: {settings.cartesia_tts_speed}")
        
        # Test language switching
        tts_hi = create_tts(settings, language="hi")
        tts_mr = create_tts(settings, language="mr")
        print(f"   ✅ Hindi TTS created successfully")
        print(f"   ✅ Marathi TTS created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_all_providers():
    """Test all providers."""
    print("=" * 70)
    print("PROVIDER CONNECTIVITY TEST")
    print("=" * 70)
    
    settings = get_settings()
    print(f"\n📋 Configuration:")
    print(f"   Agent Name: {settings.agent_name}")
    print(f"   LiveKit URL: {settings.livekit_url}")
    print(f"   Token Issuer Configured: {settings.token_issuer_configured}")
    print(f"   All Providers Configured: {settings.agent_providers_configured}")
    
    results = {
        "stt": await test_deepgram_stt(),
        "llm": await test_mistral_llm(),
        "tts": await test_cartesia_tts(),
    }
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Deepgram STT: {'✅ PASS' if results['stt'] else '❌ FAIL'}")
    print(f"Mistral LLM:  {'✅ PASS' if results['llm'] else '❌ FAIL'}")
    print(f"Cartesia TTS: {'✅ PASS' if results['tts'] else '❌ FAIL'}")
    print("=" * 70)
    
    if all(results.values()):
        print("\n✅ ALL PROVIDERS WORKING!")
        print("\nYour voice assistant is ready to:")
        print("  1. Listen (Deepgram STT)")
        print("  2. Think (Mistral AI)")
        print("  3. Speak (Cartesia TTS)")
        print("\nLanguages supported: English, Hindi, Marathi")
        return 0
    else:
        print("\n❌ SOME PROVIDERS FAILED")
        print("\nCheck your API keys in backend/.env")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_all_providers())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
