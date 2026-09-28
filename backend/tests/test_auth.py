"""Mobile OTP/session contract tests using an isolated temporary database."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import routes as auth_routes
from app.auth.models import Account, AuthBase, OneTimePasscode, WebAuthnCeremony
from app.auth.session import ensure_development_auth_schema
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


def test_demo_otp_requests_do_not_lock_a_member_out_while_correcting_the_form(auth_client: TestClient) -> None:
    """The local fixed-code demo has no SMS cost, so retries must remain usable."""

    responses = [
        auth_client.post(
            "/api/auth/otp/request",
            json={"phone_number": "9000000012", "intent": "register"},
        )
        for _ in range(6)
    ]

    assert all(response.status_code == 202 for response in responses)


def test_registration_persists_profile_only_after_otp_verification(auth_client: TestClient) -> None:
    mobile = "9123456789"
    requested = auth_client.post(
        "/api/auth/otp/request",
        json={"phone_number": mobile, "intent": "register"},
    )
    assert requested.status_code == 202

    # Requesting an OTP alone does not turn the number into an account.
    before_verification = auth_client.post(
        "/api/auth/otp/request",
        json={"phone_number": mobile, "intent": "login"},
    )
    assert before_verification.status_code == 404

    verified = auth_client.post(
        "/api/auth/otp/verify",
        json={
            "phone_number": mobile,
            "otp_code": "624251",
            "intent": "register",
            "registration": {
                "full_name": "Asha Devi",
                "state": "Maharashtra",
                "district": "Pune",
                "village_or_town": "Mulshi",
                "user_type": "farmer",
                "address": "Pashan Road",
                "cooperative_role": "Member",
            },
        },
    )
    assert verified.status_code == 200
    payload = verified.json()
    assert payload["is_new_user"] is True
    assert payload["needs_onboarding"] is False
    assert payload["full_name"] == "Asha Devi"
    assert payload["user_type"] == "farmer"


def test_account_sessions_have_a_minimum_one_hour_lifetime() -> None:
    assert Settings(jwt_access_token_minutes=60).jwt_access_token_minutes == 60
    with pytest.raises(ValidationError):
        Settings(jwt_access_token_minutes=59)


def test_development_webauthn_accepts_loopback_vite_ports_only() -> None:
    """Vite may use 5174+ when another local dev server owns 5173."""

    settings = Settings(app_env="development", web_authn_origins="http://localhost:5173")

    assert settings.web_authn_rp_id_for_origin("http://localhost:5174") == "localhost"
    assert settings.web_authn_rp_id_for_origin("http://127.0.0.1:61234") == "127.0.0.1"
    assert settings.web_authn_rp_id_for_origin("http://192.168.1.9:5174") is None
    assert settings.web_authn_rp_id_for_origin("https://example.test") is None


def test_sqlite_can_claim_a_fresh_biometric_ceremony(tmp_path) -> None:
    """SQLite timestamps are naïve, but a just-created passkey ceremony works."""

    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'passkey-ceremony.db').as_posix()}"

    async def claim() -> WebAuthnCeremony:
        engine = create_async_engine(database_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)
        async with factory() as session:
            ceremony = WebAuthnCeremony(
                id="c" * 48,
                account_id=None,
                purpose="authentication",
                challenge="test-challenge",
                rp_id="localhost",
                origin="http://localhost:5173",
                expires_at=datetime.now(UTC) + timedelta(minutes=5),
            )
            session.add(ceremony)
            await session.commit()
            claimed = await auth_routes._claim_ceremony(
                session,
                ceremony_id=ceremony.id,
                purpose="authentication",
                account_id=None,
            )
            await session.refresh(ceremony)
            assert ceremony.used_at is not None
        await engine.dispose()
        return claimed

    claimed = asyncio.run(claim())
    assert claimed.id == "c" * 48


def test_local_sqlite_schema_upgrade_preserves_existing_accounts(tmp_path) -> None:
    """A pre-passkey local database must remain usable after an app update."""

    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'legacy-sahayak.db').as_posix()}"

    async def upgrade_schema() -> Account:
        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            # Deliberately omit newer passkey columns to model an older local DB.
            await connection.execute(text("""
                CREATE TABLE sahayak_accounts (
                    id INTEGER PRIMARY KEY,
                    phone_number VARCHAR(20) UNIQUE NOT NULL,
                    full_name VARCHAR(120), state VARCHAR(100), district VARCHAR(120),
                    village_or_town VARCHAR(120), address TEXT, user_type VARCHAR(48),
                    cooperative_role VARCHAR(120), profile_completed BOOLEAN NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1, token_version INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME, updated_at DATETIME
                )
            """))
            await connection.execute(
                text("INSERT INTO sahayak_accounts (phone_number) VALUES ('+919000000012')")
            )
        await ensure_development_auth_schema(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            account = await session.scalar(select(Account).where(Account.phone_number == "+919000000012"))
        await engine.dispose()
        assert account is not None
        return account

    upgraded = asyncio.run(upgrade_schema())
    assert upgraded.face_id_enabled is False
    assert upgraded.last_mobile_verification_at is None
