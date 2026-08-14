"""Integration test cases for complete workflows."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_then_token_request():
    """Test complete workflow: check health, then request token."""
    # Step 1: Check health
    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    
    health_data = health_response.json()
    is_configured = health_data["configured"]
    
    # Step 2: Request token
    token_response = client.post("/api/token", json={
        "room_name": "integration-test",
        "participant_name": "Tester"
    })
    
    # Should succeed if configured, fail if not
    if is_configured:
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert "server_url" in token_data
        assert "participant_token" in token_data
    else:
        assert token_response.status_code == 503


def test_multiple_token_requests():
    """Test that multiple token requests work independently."""
    request1 = client.post("/api/token", json={"room_name": "room-1"})
    request2 = client.post("/api/token", json={"room_name": "room-2"})
    request3 = client.post("/api/token", json={"room_name": "room-3"})
    
    # All should have the same status (either all 200 or all 503)
    statuses = {request1.status_code, request2.status_code, request3.status_code}
    assert len(statuses) == 1  # All same status
    
    if 200 in statuses:
        # All tokens should be different
        token1 = request1.json()["participant_token"]
        token2 = request2.json()["participant_token"]
        token3 = request3.json()["participant_token"]
        
        assert token1 != token2
        assert token2 != token3
        assert token1 != token3


def test_token_request_with_same_room():
    """Test that multiple participants can join the same room."""
    room = "shared-room"
    
    request1 = client.post("/api/token", json={
        "room_name": room,
        "participant_name": "User1"
    })
    request2 = client.post("/api/token", json={
        "room_name": room,
        "participant_name": "User2"
    })
    
    # Both should succeed or both should fail
    assert request1.status_code == request2.status_code
    
    if request1.status_code == 200:
        # Tokens should be different even for same room
        token1 = request1.json()["participant_token"]
        token2 = request2.json()["participant_token"]
        assert token1 != token2


def test_cors_with_real_workflow():
    """Test CORS headers throughout a complete workflow."""
    origin = "http://localhost:5173"
    headers = {"Origin": origin}
    
    # Health check with CORS
    health_response = client.get("/api/health", headers=headers)
    assert health_response.status_code == 200
    assert "access-control-allow-origin" in health_response.headers
    
    # Token request with CORS
    token_response = client.post(
        "/api/token",
        json={"room_name": "cors-test"},
        headers={**headers, "Content-Type": "application/json"}
    )
    assert token_response.status_code in [200, 503]
    assert "access-control-allow-origin" in token_response.headers


def test_api_prefix_consistency():
    """Test that all endpoints use /api prefix consistently."""
    # Valid endpoints
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/token").status_code in [200, 503]
    
    # Without prefix should fail
    assert client.get("/health").status_code == 404
    assert client.post("/token").status_code == 404


def test_content_type_json():
    """Test that all responses have JSON content type."""
    health_response = client.get("/api/health")
    assert "application/json" in health_response.headers["content-type"]
    
    token_response = client.post("/api/token")
    assert "application/json" in token_response.headers["content-type"]


def test_error_responses_have_detail():
    """Test that error responses include detail field."""
    # Invalid room name
    response = client.post("/api/token", json={
        "room_name": "invalid room name!"
    })
    
    if response.status_code in [422, 503]:
        data = response.json()
        assert "detail" in data
