"""Mobile OTP/session contract tests using an isolated temporary database."""

from __future__ import annotations

import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import routes as auth_routes
from app.auth.models import AuthBase, OneTimePasscode
from app.auth.security import CSRF_COOKIE, CSRF_HEADER
from app.config.settings import Settings, get_settings
from app.main import app


@pytest.fixture
def auth_client(tmp_path) -> Generator[TestClient, None, None]:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'sahayak-auth.db').as_posix()}"
    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    settings = Settings(
        database_url=database_url,
        jwt_secret_key="test-only-secret",
        otp_demo_mode=True,
        otp_demo_code="624251",
    )

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)

    async def session_override() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    asyncio.run(create_schema())
    app.state._test_auth_database_url = database_url
    app.dependency_overrides[auth_routes.get_auth_session] = session_override
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        del app.state._test_auth_database_url
        asyncio.run(engine.dispose())


def test_mobile_otp_creates_hashed_code_then_establishes_a_cookie_session(auth_client: TestClient) -> None:
    mobile = "9876543210"
    requested = auth_client.post("/api/auth/otp/request", json={"phone_number": mobile})
    assert requested.status_code == 202

    # An incorrect OTP does not establish a session.
    rejected = auth_client.post(
        "/api/auth/otp/verify",
        json={"phone_number": mobile, "otp_code": "111111"},
    )
    assert rejected.status_code == 401

    verified = auth_client.post(
        "/api/auth/otp/verify",
        json={"phone_number": mobile, "otp_code": "624251"},
    )
    assert verified.status_code == 200
    payload = verified.json()
    assert payload["is_new_user"] is True
    assert payload["needs_onboarding"] is True
    assert "access_token" not in payload
    assert auth_client.cookies.get("sahayak_session")
    assert auth_client.cookies.get(CSRF_COOKIE)

    profile = auth_client.get("/api/auth/profile")
    assert profile.status_code == 200
    assert profile.json()["phone_number"] == "+919876543210"

    missing_csrf = auth_client.put("/api/auth/profile", json={"full_name": "Asha"})
    assert missing_csrf.status_code == 403

    updated = auth_client.put(
        "/api/auth/profile",
        headers={CSRF_HEADER: auth_client.cookies.get(CSRF_COOKIE)},
        json={
            "full_name": "Asha Devi",
            "state": "Maharashtra",
            "district": "Pune",
            "village_or_town": "Mulshi",
            "user_type": "farmer",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["needs_onboarding"] is False

    logged_out = auth_client.post(
        "/api/auth/logout",
        headers={CSRF_HEADER: auth_client.cookies.get(CSRF_COOKIE)},
    )
    assert logged_out.status_code == 204
    assert auth_client.get("/api/auth/profile").status_code == 401


def test_otp_codes_are_not_stored_in_plaintext(auth_client: TestClient) -> None:
    response = auth_client.post("/api/auth/otp/request", json={"phone_number": "9876543210"})
    assert response.status_code == 202

    async def load_code() -> OneTimePasscode:
        # Recreate the file-backed session through SQLAlchemy for a persistence
        # assertion without exposing this query through an HTTP endpoint.
        database_url = str(auth_client.app.state._test_auth_database_url)
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            value = await session.scalar(select(OneTimePasscode).order_by(OneTimePasscode.id.desc()))
        await engine.dispose()
        assert value is not None
        return value

    stored = asyncio.run(load_code())
    assert stored.code_hash != "624251"
    assert "624251" not in stored.code_hash
