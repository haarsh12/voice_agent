"""Async database session dependency for authenticated Sahayak API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import AuthBase
# Register the knowledge tables on the same server-owned metadata. Importing
# the models here is intentional: local development schema creation must not
# omit the knowledge audit tables while production stays migration-owned.
import app.knowledge.models  # noqa: F401
from app.config.settings import get_settings


@lru_cache
def get_engine() -> AsyncEngine | None:
    database_url = get_settings().async_database_url
    if not database_url:
        return None
    if database_url.startswith("sqlite"):
        # The local API and the offline ingestion worker legitimately share
        # one demo database. SQLite permits one writer at a time, so wait for
        # a short transaction instead of failing a source check immediately.
        # Hosted PostgreSQL continues to use its normal concurrent engine.
        return create_async_engine(database_url, connect_args={"timeout": 30})
    return create_async_engine(database_url, pool_pre_ping=True, pool_recycle=300)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False) if engine else None


def _upgrade_development_sqlite_schema(connection: Connection) -> None:
    """Add fields introduced after a local SQLite prototype was first created.

    ``create_all`` creates missing tables but intentionally never alters an
    existing one. Local Sahayak databases predate the optional passkey fields,
    so an ordinary account lookup would otherwise crash before the user can
    register or sign in. Hosted databases remain migration-owned.
    """

    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    upgrades_by_table = {
        "sahayak_accounts": {
            "face_id_enabled": "BOOLEAN NOT NULL DEFAULT 0",
            "last_mobile_verification_at": "DATETIME",
        },
        # Local databases can predate a registry revision. Production Postgres
        # remains migration-owned; this only keeps the ignored SQLite demo
        # database compatible with checked-in SQLAlchemy models.
        "sahayak_knowledge_sources": {
            "discovery_path_prefixes": "JSON NOT NULL DEFAULT '[]'",
            "max_documents_per_check": "INTEGER NOT NULL DEFAULT 25",
            "expected_categories": "JSON NOT NULL DEFAULT '[]'",
        },
        "sahayak_knowledge_document_versions": {
            "coverage_categories": "JSON NOT NULL DEFAULT '[]'",
        },
    }
    for table, upgrades in upgrades_by_table.items():
        if table not in tables:
            continue
        columns = {column["name"] for column in inspector.get_columns(table)}
        for name, definition in upgrades.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

    if "sahayak_knowledge_source_checks" in tables:
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "sahayak_knowledge_source_checks_one_open_per_source "
                "ON sahayak_knowledge_source_checks (source_key) "
                "WHERE completed_at IS NULL"
            )
        )


async def ensure_development_auth_schema(engine: AsyncEngine) -> None:
    """Create and safely upgrade the Git-ignored local authentication schema."""

    async with engine.begin() as connection:
        await connection.run_sync(AuthBase.metadata.create_all)
        await connection.run_sync(_upgrade_development_sqlite_schema)


async def get_auth_session() -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    engine = get_engine()
    session_factory = get_session_factory()
    if session_factory is None or engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account services are not configured yet.",
        )
    # Development uses a local, Git-ignored SQLite file for a usable prototype.
    # Hosted environments must run migrations explicitly instead.
    if not settings.is_production and settings.async_database_url and settings.async_database_url.startswith("sqlite"):
        await ensure_development_auth_schema(engine)
    async with session_factory() as session:
        yield session
