#!/usr/bin/env python3
"""Test runner script with detailed reporting."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path


def main() -> int:
    """Run all tests and display results."""
    backend_dir = Path(__file__).parent
    
    print("=" * 70)
    print("VYAMIT VOICE BACKEND - TEST SUITE")
    print("=" * 70)
    print()
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed!")
        print("   Install it with: pip install pytest pytest-cov httpx")
        return 1
    
    print("Running tests...")
    print()
    
    # Run pytest with verbose output
    args = [
        "-v",  # Verbose
        "--tb=short",  # Shorter traceback format
        "--color=yes",  # Colored output
        "-ra",  # Show summary of all test outcomes
        "tests/",
    ]
    
    result = pytest.main(args)
    
    print()
    print("=" * 70)
    
    if result == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    sys.exit(main())
