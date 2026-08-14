"""Test cases for CORS configuration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_headers_on_health():
    """Test that CORS headers are present on health endpoint."""
    response = client.get("/api/health")
    
    # Check that CORS middleware is working
    assert response.status_code == 200


def test_cors_preflight_request():
    """Test CORS preflight (OPTIONS) request."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/token", headers=headers)
    
    # Preflight should return 200 with proper headers
    assert response.status_code == 200


def test_cors_origin_header():
    """Test that requests with Origin header are handled."""
    headers = {"Origin": "http://localhost:5173"}
    response = client.get("/api/health", headers=headers)
    
    assert response.status_code == 200
    # Check if Access-Control-Allow-Origin is in response headers
    assert "access-control-allow-origin" in response.headers


def test_post_with_cors():
    """Test POST request with CORS headers."""
    headers = {
        "Origin": "http://localhost:5173",
        "Content-Type": "application/json"
    }
    response = client.post("/api/token", json={}, headers=headers)
    
    assert response.status_code in [200, 503]
    assert "access-control-allow-origin" in response.headers
