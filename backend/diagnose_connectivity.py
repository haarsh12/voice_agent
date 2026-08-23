"""Diagnose LiveKit connectivity issues."""

import asyncio
import os
import socket
from urllib.parse import urlparse

import aiohttp
from dotenv import load_dotenv

load_dotenv()


async def test_dns_resolution(hostname: str) -> bool:
    """Test if hostname can be resolved."""
    try:
        print(f"\n🔍 Testing DNS resolution for {hostname}...")
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ DNS resolved to: {ip}")
        return True
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False


async def test_https_connection(url: str) -> bool:
    """Test HTTPS connection to LiveKit."""
    try:
        print(f"\n🔍 Testing HTTPS connection to {url}...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url.replace("wss://", "https://"), timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"   ✅ HTTPS connection successful: Status {resp.status}")
                return True
    except asyncio.TimeoutError:
        print(f"   ❌ Connection timeout - network/firewall issue")
        return False
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        return False


async def test_websocket_connection(url: str) -> bool:
    """Test WebSocket connection to LiveKit."""
    try:
        print(f"\n🔍 Testing WebSocket connection to {url}...")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url, timeout=aiohttp.ClientTimeout(total=10)) as ws:
                print(f"   ✅ WebSocket connection successful")
                return True
    except asyncio.TimeoutError:
        print(f"   ❌ WebSocket timeout - firewall may be blocking WSS")
        return False
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ WebSocket connection error: {e}")
        return False
    except Exception as e:
        print(f"   ⚠️ WebSocket error: {e}")
        return False


async def check_proxy_settings():
    """Check for proxy settings."""
    print(f"\n🔍 Checking proxy settings...")
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy or https_proxy:
        print(f"   ⚠️ Proxy detected:")
        if http_proxy:
            print(f"      HTTP_PROXY: {http_proxy}")
        if https_proxy:
            print(f"      HTTPS_PROXY: {https_proxy}")
        print(f"   💡 Proxies may interfere with WebSocket connections")
    else:
        print(f"   ✅ No proxy configured")


async def test_google_cloud_connectivity():
    """Test Google Cloud API connectivity."""
    print(f"\n🔍 Testing Google Cloud API connectivity...")
    
    urls = [
        "https://speech.googleapis.com",
        "https://texttospeech.googleapis.com",
        "https://generativelanguage.googleapis.com",
    ]
    
    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    print(f"   ✅ {url}: Status {resp.status}")
        except Exception as e:
            print(f"   ❌ {url}: {e}")


async def main():
    """Run all diagnostics."""
    print("="*70)
    print("🔧 LiveKit Connectivity Diagnostics")
    print("="*70)
    
    livekit_url = os.getenv("LIVEKIT_URL", "wss://vyamit-cpoa7nzp.livekit.cloud")
    
    print(f"\n📋 Configuration:")
    print(f"   LIVEKIT_URL: {livekit_url}")
    print(f"   AGENT_NAME: {os.getenv('AGENT_NAME', 'vyamit-voice')}")
    
    # Parse URL
    parsed = urlparse(livekit_url)
    hostname = parsed.hostname
    
    # Run tests
    await check_proxy_settings()
    
    dns_ok = await test_dns_resolution(hostname)
    if not dns_ok:
        print("\n❌ DNS resolution failed - check internet connection")
        return
    
    https_ok = await test_https_connection(livekit_url)
    ws_ok = await test_websocket_connection(livekit_url)
    
    await test_google_cloud_connectivity()
    
    print("\n" + "="*70)
    print("📊 Summary:")
    print("="*70)
    
    if dns_ok and https_ok and ws_ok:
        print("✅ All connectivity tests passed!")
        print("💡 The issue may be:")
        print("   1. LiveKit API credentials incorrect")
        print("   2. Temporary network issue")
        print("   3. LiveKit server issue")
    elif not ws_ok:
        print("❌ WebSocket connection failed!")
        print("💡 Possible causes:")
        print("   1. Corporate firewall blocking WSS (port 443)")
        print("   2. Antivirus/security software blocking")
        print("   3. Network proxy interfering")
        print("\n🔧 Solutions:")
        print("   1. Check firewall settings")
        print("   2. Try from different network")
        print("   3. Contact IT to allow wss://vyamit-cpoa7nzp.livekit.cloud")
    else:
        print("❌ Network connectivity issues detected")
        print("💡 Check your internet connection and firewall settings")


if __name__ == "__main__":
    asyncio.run(main())
