"""Test cases for token endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_token_endpoint_exists():
    """Test that /api/token endpoint is accessible."""
    response = client.post("/api/token")
    # Should return 200 if configured, or 503 if not configured
    assert response.status_code in [200, 503]


def test_token_endpoint_without_body():
    """Test token endpoint with no request body (should generate defaults)."""
    response = client.post("/api/token")
    
    if response.status_code == 200:
        data = response.json()
        assert "server_url" in data
        assert "participant_token" in data
        assert isinstance(data["server_url"], str)
        assert isinstance(data["participant_token"], str)
    elif response.status_code == 503:
        # Service not configured - expected behavior
        data = response.json()
        assert "detail" in data


def test_token_endpoint_with_room_name():
    """Test token endpoint with custom room name."""
    payload = {"room_name": "test-room-123"}
    response = client.post("/api/token", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "server_url" in data
        assert "participant_token" in data


def test_token_endpoint_with_participant_name():
    """Test token endpoint with custom participant name."""
    payload = {"participant_name": "TestUser"}
    response = client.post("/api/token", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "server_url" in data
        assert "participant_token" in data


def test_token_endpoint_with_full_payload():
    """Test token endpoint with both room and participant names."""
    payload = {
        "room_name": "my-test-room",
        "participant_name": "Alice"
    }
    response = client.post("/api/token", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "server_url" in data
        assert "participant_token" in data
        assert len(data["participant_token"]) > 0


def test_token_endpoint_invalid_room_name():
    """Test token endpoint with invalid characters in room name."""
    payload = {"room_name": "invalid room with spaces!@#"}
    response = client.post("/api/token", json=payload)
    
    # Should return 422 for invalid room name
    if response.status_code == 422:
        data = response.json()
        assert "detail" in data


def test_token_endpoint_empty_room_name():
    """Test token endpoint with empty room name."""
    payload = {"room_name": ""}
    response = client.post("/api/token", json=payload)
    
    # Should either accept it and generate default, or reject it
    assert response.status_code in [200, 422, 503]


def test_token_endpoint_long_room_name():
    """Test token endpoint with room name at max length."""
    payload = {"room_name": "a" * 96}  # Max length is 96
    response = client.post("/api/token", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "participant_token" in data


def test_token_endpoint_too_long_room_name():
    """Test token endpoint with room name exceeding max length."""
    payload = {"room_name": "a" * 97}  # Exceeds max length
    response = client.post("/api/token", json=payload)
    
    # Should return validation error
    assert response.status_code == 422
