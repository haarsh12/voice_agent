#!/usr/bin/env python3
"""Setup verification script - checks if everything is ready to run."""

from __future__ import annotations

import sys
from pathlib import Path


def check_python_version():
    """Check Python version is >= 3.10."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version >= (3, 10):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need >= 3.10)")
        return False


def check_imports():
    """Check if required packages can be imported."""
    print("\n🔍 Checking required packages...")
    
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "pydantic_settings": "Pydantic Settings",
        "livekit": "LiveKit",
        "dotenv": "python-dotenv",
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - not installed")
            all_ok = False
    
    return all_ok


def check_test_packages():
    """Check if test packages are installed."""
    print("\n🔍 Checking test packages...")
    
    packages = {
        "pytest": "pytest",
        "httpx": "httpx (required by TestClient)",
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} - not installed (optional for testing)")
            all_ok = False
    
    return all_ok


def check_app_structure():
    """Check if app directory structure is correct."""
    print("\n🔍 Checking app structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/api/routes.py",
        "app/config/settings.py",
        "app/services/token_issuer.py",
        "app/agent/runner.py",
        "app/agent/providers.py",
    ]
    
    all_ok = True
    backend_dir = Path(__file__).parent
    
    for file_path in required_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - missing")
            all_ok = False
    
    return all_ok


def check_test_structure():
    """Check if test directory structure is correct."""
    print("\n🔍 Checking test structure...")
    
    test_files = [
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_imports.py",
        "tests/test_main_app.py",
        "tests/test_health_endpoint.py",
        "tests/test_token_endpoint.py",
        "tests/test_configuration.py",
    ]
    
    all_ok = True
    backend_dir = Path(__file__).parent
    
    for file_path in test_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} - missing")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check if .env file exists."""
    print("\n🔍 Checking environment configuration...")
    
    backend_dir = Path(__file__).parent
    env_files = [
        backend_dir / ".env",
        backend_dir.parent / ".env",
    ]
    
    found = False
    for env_file in env_files:
        if env_file.exists():
            print(f"   ✅ Found {env_file.relative_to(backend_dir.parent)}")
            found = True
            break
    
    if not found:
        print("   ⚠️  No .env file found (will use defaults)")
    
    return True  # Not critical


def check_app_imports():
    """Try to import the FastAPI app."""
    print("\n🔍 Checking app can be imported...")
    
    try:
        from app.main import app
        print("   ✅ FastAPI app imported successfully")
        print(f"   ✅ App title: {app.title}")
        print(f"   ✅ App version: {app.version}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to import app: {e}")
        return False


def check_settings():
    """Try to load settings."""
    print("\n🔍 Checking settings configuration...")
    
    try:
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"   ✅ Settings loaded")
        print(f"   ✅ Agent name: {settings.agent_name}")
        print(f"   ✅ API host: {settings.api_host}:{settings.api_port}")
        print(f"   ℹ️  LiveKit configured: {settings.token_issuer_configured}")
        print(f"   ℹ️  All providers configured: {settings.agent_providers_configured}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to load settings: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 70)
    print("VYAMIT VOICE BACKEND - SETUP VERIFICATION")
    print("=" * 70)
    
    checks = [
        check_python_version(),
        check_imports(),
        check_app_structure(),
        check_app_imports(),
        check_settings(),
        check_env_file(),
        check_test_structure(),
        check_test_packages(),
    ]
    
    print("\n" + "=" * 70)
    
    critical_checks = checks[:5]  # First 5 are critical
    
    if all(critical_checks):
        print("✅ ALL CRITICAL CHECKS PASSED!")
        print("\nYou can now:")
        print("  1. Run the server: uvicorn app.main:app --reload")
        print("  2. Run tests: pytest or python run_tests.py")
        print("  3. Check API docs: http://127.0.0.1:8000/docs")
    else:
        print("❌ SOME CRITICAL CHECKS FAILED")
        print("\nPlease fix the issues above before running the application.")
        return 1
    
    if not all(checks):
        print("\n⚠️  Some optional checks failed (see above)")
    
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
