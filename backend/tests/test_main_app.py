"""Test cases for main FastAPI application."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app


def test_app_is_fastapi_instance():
    """Test that app is a FastAPI instance."""
    assert isinstance(app, FastAPI)


def test_app_has_title():
    """Test that app has a title configured."""
    assert hasattr(app, "title")
    assert app.title == "Vyamit Voice Test API"


def test_app_has_version():
    """Test that app has a version configured."""
    assert hasattr(app, "version")
    assert app.version == "0.1.0"


def test_app_has_cors_middleware():
    """Test that CORS middleware is configured."""
    # Check middleware stack
    assert len(app.user_middleware) > 0


def test_app_has_router():
    """Test that API router is included."""
    # FastAPI 0.141 keeps an included router as an internal route wrapper.
    # Flatten that wrapper for this structural assertion while remaining
    # compatible with FastAPI versions that expose APIRoutes directly.
    routes = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            routes.append(path)
            continue
        routes.extend(child.path for child in getattr(route, "original_router", ()).routes)
    assert "/api/health" in routes
    assert "/api/token" in routes


def test_root_endpoint_not_found():
    """Test that root endpoint returns 404 (not configured)."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 404


def test_invalid_endpoint_not_found():
    """Test that invalid endpoints return 404."""
    client = TestClient(app)
    response = client.get("/api/invalid")
    assert response.status_code == 404


def test_app_accepts_get_requests():
    """Test that app accepts GET requests."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200


def test_app_accepts_post_requests():
    """Test that app accepts POST requests."""
    client = TestClient(app)
    response = client.post("/api/token")
    assert response.status_code in [200, 503]


def test_openapi_schema_exists():
    """Test that OpenAPI schema is generated."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


def test_docs_endpoint_exists():
    """Test that API documentation endpoint exists."""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint_exists():
    """Test that ReDoc documentation endpoint exists."""
    client = TestClient(app)
    response = client.get("/redoc")
    assert response.status_code == 200
