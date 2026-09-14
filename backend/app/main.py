"""FastAPI application used by the Vite frontend for secure token issuance."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config.settings import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()
logger = logging.getLogger("sahayak.main")

settings.require_runtime_security()
app = FastAPI(title="Sahayak AI API", version="0.2.0")

# Debug middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Allowed origins: {settings.allowed_origins}")
    logger.info(f"Origin regex: {settings.cors_origin_regex}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

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

# Only include auth routes if database is configured
if settings.async_database_url:
    try:
        from app.auth.routes import router as auth_router
        app.include_router(auth_router)
        logger.info("Auth routes enabled (database configured)")
    except Exception as e:
        logger.warning(f"Auth routes disabled due to error: {e}")
else:
    logger.info("Auth routes disabled (no database configured)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
