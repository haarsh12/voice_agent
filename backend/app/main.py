"""FastAPI application used by the Vite frontend for secure token issuance."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.services_routes import router as services_router
from app.admin.routes import router as admin_router
from app.auth.routes import router as auth_router
from app.auth.session import get_session_factory
from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.knowledge.routes import router as knowledge_router
from app.grievances.routes import router as grievances_router
from app.schemes.routes import router as schemes_router
from app.schemes.repository import SchemeRepository

settings = get_settings()
configure_logging()
logger = logging.getLogger("sahayak.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize schemes from knowledge base on startup if needed."""
    logger.info("sahayak_api_startup")
    
    # Skip expensive sync on every startup - only run manually or via admin API
    # To manually sync: run `python -c "import asyncio; from app.schemes.repository import SchemeRepository; from app.auth.session import get_session_factory; asyncio.run(sync())"`
    # session_factory = get_session_factory()
    # if session_factory is not None:
    #     try:
    #         async with session_factory() as session:
    #             count = await SchemeRepository(session).sync_current_documents()
    #             logger.info("scheme_catalog_startup_sync changed=%s", count)
    #     except Exception:
    #         logger.warning("scheme_catalog_startup_sync_failed", exc_info=True)
    
    yield
    
    logger.info("sahayak_api_shutdown")


settings.require_runtime_security()
app = FastAPI(title="Sahayak AI API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Browser token issuance is limited to the deployment's configured web
    # origins. LiveKit credentials and service-account credentials remain
    # server-only regardless, but an allowlist prevents another site from
    # calling this API through a visitor's browser.
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# Keep the router attached through FastAPI so application-level dependency
# overrides (used by tests and deployment integrations) work correctly.
app.include_router(router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(knowledge_router)
app.include_router(schemes_router)
app.include_router(services_router)
app.include_router(grievances_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
