#!/usr/bin/env python3
"""Test Flutter app connectivity to backend."""

import requests
import json
from pathlib import Path

def test_health():
    """Test health endpoint."""
    print("=" * 70)
    print("TESTING FLUTTER APP CONNECTIVITY")
    print("=" * 70)
    
    ip = "10.217.65.207"
    port = 8000
    base_url = f"http://{ip}:{port}"
    
    print(f"\n1️⃣  Testing Health Endpoint...")
    print(f"   URL: {base_url}/api/health")
    
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ✅ Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print(f"\n2️⃣  Testing Token Endpoint...")
    print(f"   URL: {base_url}/api/token")
    
    try:
        response = requests.post(
            f"{base_url}/api/token",
            json={
                "room_name": "test-flutter-room",
                "participant_name": "Test User"
            },
            timeout=10
        )
        print(f"   ✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"   ✅ Server URL: {data.get('server_url')}")
        print(f"   ✅ Token: {data.get('participant_token')[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print(f"\n3️⃣  Network Configuration...")
    print(f"   Backend IP: {ip}")
    print(f"   Backend Port: {port}")
    print(f"   Flutter App baseUrl: http://{ip}:{port}")
    
    print("\n" + "=" * 70)
    print("✅ ALL CONNECTIVITY TESTS PASSED!")
    print("=" * 70)
    print("\nFlutter app should be able to connect.")
    print("\nPOSSIBLE ISSUES:")
    print("  1. Phone not on same WiFi network")
    print("  2. Windows Firewall blocking port 8000")
    print("  3. Agent worker not running")
    print("\nTO START AGENT WORKER:")
    print("  cd backend")
    print("  .venv\\Scripts\\activate")
    print("  python -m app.agent.runner start")
    
    return True

if __name__ == "__main__":
    test_health()
