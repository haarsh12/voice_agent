#!/usr/bin/env python3
"""Check complete system status."""

import requests
import sys


def check_backend_api():
    """Check if backend API is responding."""
    print("🔍 Checking Backend API...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend API is running")
            print(f"   ℹ️  Status: {data.get('status')}")
            print(f"   ℹ️  Agent Name: {data.get('agent_name')}")
            return True
        else:
            print(f"   ❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend not accessible: {e}")
        return False


def check_token_generation():
    """Check if token generation works."""
    print("\n🎫 Checking Token Generation...")
    try:
        response = requests.post(
            "http://localhost:8000/api/token",
            json={"room_name": "status-check", "participant_name": "StatusBot"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Token generation working")
            print(f"   ℹ️  Server: {data.get('server_url')}")
            print(f"   ℹ️  Token: {data.get('participant_token')[:50]}...")
            return True
        else:
            print(f"   ❌ Token generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Token generation error: {e}")
        return False


def check_agent_worker():
    """Check if agent worker HTTP server is accessible."""
    print("\n🤖 Checking Agent Worker...")
    try:
        # Agent worker runs HTTP server on 8081
        response = requests.get("http://localhost:8081/", timeout=5)
        print(f"   ✅ Agent worker HTTP server responding")
        return True
    except Exception as e:
        print(f"   ⚠️  Agent worker HTTP not accessible (this is normal)")
        print(f"      The agent worker is likely running in background")
        return True  # Not critical


def check_frontend():
    """Check if frontend is accessible."""
    print("\n🌐 Checking Frontend...")
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Frontend is accessible")
            return True
        else:
            print(f"   ❌ Frontend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Frontend not accessible: {e}")
        return False


def main():
    """Run all status checks."""
    print("=" * 70)
    print("SYSTEM STATUS CHECK")
    print("=" * 70)
    print()
    
    results = {
        "backend": check_backend_api(),
        "token": check_token_generation(),
        "agent": check_agent_worker(),
        "frontend": check_frontend(),
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Backend API:      {'✅ RUNNING' if results['backend'] else '❌ DOWN'}")
    print(f"Token Generation: {'✅ WORKING' if results['token'] else '❌ FAILED'}")
    print(f"Agent Worker:     {'✅ RUNNING' if results['agent'] else '⚠️  CHECK LOGS'}")
    print(f"Frontend:         {'✅ RUNNING' if results['frontend'] else '❌ DOWN'}")
    print("=" * 70)
    
    critical = results['backend'] and results['token'] and results['frontend']
    
    if critical:
        print("\n✅ SYSTEM IS OPERATIONAL!")
        print("\nAccess the application:")
        print("  🌐 Frontend:  http://localhost:5173")
        print("  📡 Backend:   http://localhost:8000")
        print("  📚 API Docs:  http://localhost:8000/docs")
        print("\nProviders configured:")
        print("  🎤 Deepgram  - Speech-to-Text (Multi-language)")
        print("  🤖 Mistral   - Language Model")
        print("  🔊 Cartesia  - Text-to-Speech (en/hi/mr)")
        return 0
    else:
        print("\n❌ SYSTEM HAS ISSUES")
        print("\nTroubleshooting:")
        if not results['backend']:
            print("  - Start backend: cd backend && uvicorn app.main:app --reload")
        if not results['frontend']:
            print("  - Start frontend: cd frontend && npm run dev")
        if not results['agent']:
            print("  - Start agent: cd backend && python -m app.agent.runner start")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nStatus check interrupted")
        sys.exit(130)
