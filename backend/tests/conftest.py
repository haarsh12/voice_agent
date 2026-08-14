"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient instance for all tests."""
    return TestClient(app)


@pytest.fixture
def test_room_name() -> str:
    """Provide a test room name."""
    return "test-room-pytest"


@pytest.fixture
def test_participant_name() -> str:
    """Provide a test participant name."""
    return "TestUser"


@pytest.fixture
def valid_token_request() -> dict:
    """Provide a valid token request payload."""
    return {
        "room_name": "test-room-123",
        "participant_name": "Alice"
    }


@pytest.fixture
def invalid_token_request() -> dict:
    """Provide an invalid token request payload."""
    return {
        "room_name": "invalid room name with spaces!",
        "participant_name": "Bob"
    }
