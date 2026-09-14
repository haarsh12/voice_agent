"""Async database session dependency for authenticated Sahayak API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import AuthBase
from app.config.settings import get_settings


@lru_cache
def get_engine() -> AsyncEngine | None:
    database_url = get_settings().async_database_url
    if not database_url:
        return None
    if database_url.startswith("sqlite"):
        return create_async_engine(database_url)
    return create_async_engine(database_url, pool_pre_ping=True, pool_recycle=300)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False) if engine else None


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
        async with engine.begin() as connection:
            await connection.run_sync(AuthBase.metadata.create_all)
    async with session_factory() as session:
        yield session
