"""Focused security coverage for the knowledge-administration boundary."""

from __future__ import annotations

from argon2 import PasswordHasher
from pydantic import SecretStr

from app.config.settings import Settings, get_settings
from app.main import app


def _admin_settings() -> Settings:
    return Settings(
        jwt_secret_key=SecretStr("test-only-admin-session-signing-key"),
        admin_id="test-admin",
        admin_password_hash=SecretStr(PasswordHasher().hash("test-only-admin-password")),
        qdrant_url="",
    )


def test_admin_dashboard_requires_an_isolated_admin_session(client) -> None:
    settings = _admin_settings()
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        denied = client.get("/api/admin/knowledge-dashboard")
        assert denied.status_code == 401

        rejected = client.post(
            "/api/admin/session",
            json={"admin_id": "test-admin", "password": "wrong-password"},
        )
        assert rejected.status_code == 401

        signed_in = client.post(
            "/api/admin/session",
            json={"admin_id": "test-admin", "password": "test-only-admin-password"},
        )
        assert signed_in.status_code == 200, signed_in.text
        assert signed_in.json() == {"authenticated": True}
        assert "sahayak_admin_session" in signed_in.headers.get("set-cookie", "")
        assert "HttpOnly" in signed_in.headers.get("set-cookie", "")

        dashboard = client.get("/api/admin/knowledge-dashboard")
        assert dashboard.status_code == 200, dashboard.text
        payload = dashboard.json()
        assert payload["storage"]["vector_index"] == "not_configured"
        assert "sources" in payload
        assert "content_hash" not in str(payload)
        assert "vector" not in str(payload["recent_documents"])
    finally:
        app.dependency_overrides.clear()


def test_admin_logout_requires_its_own_csrf_token(client) -> None:
    settings = _admin_settings()
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        signed_in = client.post(
            "/api/admin/session",
            json={"admin_id": "test-admin", "password": "test-only-admin-password"},
        )
        assert signed_in.status_code == 200
        forbidden = client.delete("/api/admin/session")
        assert forbidden.status_code == 403
        csrf = client.cookies.get("sahayak_admin_csrf")
        assert csrf
        signed_out = client.delete("/api/admin/session", headers={"X-Sahayak-Admin-CSRF": csrf})
        assert signed_out.status_code == 204
        assert client.get("/api/admin/knowledge-dashboard").status_code == 401
    finally:
        app.dependency_overrides.clear()
