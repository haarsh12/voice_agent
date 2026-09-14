"""FastAPI application used by the Vite frontend for secure token issuance."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.auth.routes import router as auth_router
from app.config.settings import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()

settings.require_runtime_security()
app = FastAPI(title="Sahayak AI API", version="0.2.0")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
