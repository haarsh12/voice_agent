"""Test cases for health endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_exists():
    """Test that /api/health endpoint is accessible."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json():
    """Test that health endpoint returns valid JSON."""
    response = client.get("/api/health")
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)


def test_health_endpoint_has_required_fields():
    """Test that health endpoint returns all required fields."""
    response = client.get("/api/health")
    data = response.json()
    
    assert "status" in data
    assert "agent_name" in data
    assert "configured" in data


def test_health_endpoint_status_ok():
    """Test that health endpoint returns status ok."""
    response = client.get("/api/health")
    data = response.json()
    
    assert data["status"] == "ok"


def test_health_endpoint_agent_name():
    """Test that health endpoint returns agent name."""
    response = client.get("/api/health")
    data = response.json()
    
    assert isinstance(data["agent_name"], str)
    assert len(data["agent_name"]) > 0


def test_health_endpoint_configured_is_boolean():
    """Test that configured field is a boolean."""
    response = client.get("/api/health")
    data = response.json()
    
    assert isinstance(data["configured"], bool)
