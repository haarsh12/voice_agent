"""Typed, environment-only configuration for the API and voice agent."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import secrets
from urllib.parse import urlparse

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingConfigurationError(RuntimeError):
    """Raised when a server-side capability is requested without its credentials."""


class Settings(BaseSettings):
    """All runtime settings. No provider secret is ever exposed to the frontend."""

    model_config = SettingsConfigDict(
        # The project began with a root-level .env. Keep that convenient
        # local-dev convention, while allowing backend/.env to override it.
        env_file=("../.env", "../.env.local", ".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # The voice worker uses this local API only to obtain the authenticated,
    # short-lived guest context that was bound into the participant token.
    # Keep it private to the deployment; it is never sent to the browser.
    guest_session_api_url: str = "http://127.0.0.1:8000"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    livekit_url: str = ""
    livekit_api_key: SecretStr | None = None
    livekit_api_secret: SecretStr | None = None
    agent_name: str = "sahayak-ai"

    # Mobile-account credentials and database access are server-only. The
    # browser uses an HttpOnly session cookie and never receives these values.
    database_url: SecretStr | None = None
    jwt_secret_key: SecretStr | None = None
    # Account sessions must remain usable for at least one hour. The default
    # is seven days; deployments may shorten it, but never below 60 minutes.
    jwt_access_token_minutes: int = Field(default=60 * 24 * 7, ge=60, le=60 * 24 * 30)
    otp_demo_mode: bool = True
    otp_demo_code: SecretStr | None = None
    fast2sms_api_key: SecretStr | None = None
    fast2sms_base_url: str = "https://www.fast2sms.com/dev/bulkV2"

    # WebAuthn keeps biometric data on the member's device. Production must
    # name its real HTTPS origin and RP ID; local development can use one of
    # the existing explicit Vite origins.
    web_authn_rp_name: str = "Sahayak AI"
    web_authn_rp_id: str = ""
    web_authn_origins: str = ""

    # Google Cloud STT configuration
    google_application_credentials: str | None = None
    google_stt_language: str = "hi-IN"
    # Fallback model for integrations outside the selector. The live selector
    # uses the explicit, provider-compatible profile for each language.
    google_stt_model: str = "latest_long"
    google_stt_location: str = "global"
    google_keyterms: str = "Sahayak,सहायक,नमस्ते,धन्यवाद,सहकारी,पीएसीएस"

    # Gemini runs through Vertex AI using GOOGLE_APPLICATION_CREDENTIALS. The
    # project can be inferred from a service-account key, but specifying it is
    # useful for workload identity and other non-key credential sources.
    google_cloud_project: str = ""
    google_cloud_location: str = "global"
    gemini_model: str = "gemini-3.5-flash"
    gemini_temperature: float = Field(default=0.35, ge=0, le=2)

    # Knowledge-engine configuration. Qdrant is an internal service only: its
    # endpoint and optional API key are never returned by any API route and
    # must never use a VITE_ environment variable.
    qdrant_url: str = ""
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "sahayak_verified_knowledge"
    knowledge_embedding_model: str = "text-embedding-004"
    knowledge_embedding_dimensions: int = Field(default=768, ge=64, le=4096)
    knowledge_retrieval_limit: int = Field(default=8, ge=1, le=25)
    knowledge_fetch_timeout_seconds: float = Field(default=20.0, ge=1.0, le=60.0)
    knowledge_max_document_bytes: int = Field(default=8 * 1024 * 1024, ge=64 * 1024, le=32 * 1024 * 1024)

    # Google Cloud TTS defaults. The live selector supplies the locale-specific
    # Chirp 3 HD voice for every supported language.
    google_tts_language: str = "hi-IN"  # Default to Hindi
    google_tts_voice: str = "hi-IN-Neural2-A"  # High-quality Neural2 voice
    google_tts_speed: float = Field(default=1.0, ge=0.25, le=4.0)
    google_tts_pitch: float = Field(default=0.0, ge=-20.0, le=20.0)
    
    # Optional: Cartesia TTS (kept for fallback/comparison)
    cartesia_api_key: SecretStr | None = None
    cartesia_tts_model: str = "sonic-3"
    cartesia_voice_id: str = "f786b574-daa5-4673-aa0c-cbe3e8534c02"
    cartesia_tts_language: str = "en"
    cartesia_tts_speed: float = Field(default=1.0, ge=0.6, le=1.5)

    enable_enhanced_noise_cancellation: bool = False

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_web_authn_origins(self) -> list[str]:
        configured = [origin.strip() for origin in self.web_authn_origins.split(",") if origin.strip()]
        return configured or self.allowed_origins

    def web_authn_rp_id_for_origin(self, origin: str | None) -> str | None:
        """Return an RP ID only for a trusted WebAuthn browser origin.

        Vite moves to the next free port when 5173 is already in use.  It is
        still the same local Sahayak site, so development accepts loopback
        origins on any port.  This exception is intentionally limited to
        localhost/loopback; LAN and public origins must remain explicitly
        configured (and production requires HTTPS).
        """

        if not origin:
            return None
        parsed = urlparse(origin)
        host = (parsed.hostname or "").lower().rstrip(".")
        is_origin = (
            parsed.scheme in {"http", "https"}
            and bool(host)
            and parsed.username is None
            and parsed.password is None
            and parsed.path in {"", "/"}
            and not parsed.params
            and not parsed.query
            and not parsed.fragment
        )
        if not is_origin:
            return None
        is_loopback = host in {"localhost", "127.0.0.1", "::1"}
        is_configured_origin = origin in self.allowed_web_authn_origins
        if not is_configured_origin and not (not self.is_production and is_loopback):
            return None
        if self.is_production and parsed.scheme != "https":
            return None

        rp_id = self.web_authn_rp_id.strip().lower().rstrip(".") or (
            host if not self.is_production else ""
        )
        if not rp_id or (host != rp_id and not host.endswith(f".{rp_id}")):
            return None
        return rp_id

    @property
    def cors_origin_regex(self) -> str | None:
        """Allow ordinary local/LAN Vite origins only while developing.

        Credentials are used for the Sahayak session, so a wildcard origin is
        intentionally never used. Developers do, however, often run Vite on a
        different port or access it through a private LAN address when testing
        on a phone. This narrowly scoped development expression avoids failed
        preflight requests in those cases. Production remains explicit-only.
        """
        if self.is_production:
            return None
        return (
            r"^https?://(?:"
            r"localhost|127\.0\.0\.1|\[::1\]|"
            r"10(?:\.\d{1,3}){3}|"
            r"192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
            r")(?::\d{1,5})?$"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def async_database_url(self) -> str | None:
        if self.database_url is None:
            # The prototype should work immediately for local demonstrations
            # without provisioning hosted infrastructure. This file is ignored
            # by Git and is never used in production.
            return "sqlite+aiosqlite:///./sahayak-dev.db" if not self.is_production else None
        value = self.database_url.get_secret_value().strip()
        if value.startswith("postgres://"):
            value = "postgresql://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return (
                "postgresql+asyncpg://" + value.removeprefix("postgresql://")
            ).replace("sslmode=", "ssl=")
        return value or None

    def require_jwt_secret(self) -> str:
        if self.jwt_secret_key is None or not self.jwt_secret_key.get_secret_value().strip():
            raise MissingConfigurationError("JWT_SECRET_KEY must be configured on the server.")
        return self.jwt_secret_key.get_secret_value()

    def require_demo_otp_code(self) -> str:
        # Keep the test code backend-owned. Production startup rejects demo
        # mode, so it can never become a production authentication path.
        value = self.otp_demo_code.get_secret_value().strip() if self.otp_demo_code else "624251"
        if len(value) != 6 or not value.isdigit():
            raise MissingConfigurationError("OTP_DEMO_CODE must be exactly six digits.")
        return value

    def require_sms_delivery(self) -> None:
        if self.otp_demo_mode:
            return
        self._require("FAST2SMS_API_KEY", self.fast2sms_api_key)

    def require_runtime_security(self) -> None:
        if not self.is_production:
            return
        self.require_jwt_secret()
        if not self.async_database_url:
            raise MissingConfigurationError("DATABASE_URL must be configured in production.")
        if self.otp_demo_mode:
            raise MissingConfigurationError("OTP_DEMO_MODE must be disabled in production.")
        if not self.allowed_origins or any(not origin.startswith("https://") for origin in self.allowed_origins):
            raise MissingConfigurationError("CORS_ORIGINS must contain explicit HTTPS origins in production.")
        if self.web_authn_origins and (
            not self.web_authn_rp_id.strip()
            or any(not origin.startswith("https://") for origin in self.allowed_web_authn_origins)
        ):
            raise MissingConfigurationError(
                "WEB_AUTHN_RP_ID and HTTPS WEB_AUTHN_ORIGINS are required when device biometric sign-in is enabled."
            )

    @property
    def keyterms(self) -> list[str]:
        return [term.strip() for term in self.google_keyterms.split(",") if term.strip()]

    @property
    def token_issuer_configured(self) -> bool:
        return all(
            self._has_value(value)
            for value in (self.livekit_url, self.livekit_api_key, self.livekit_api_secret)
        )

    @property
    def agent_providers_configured(self) -> bool:
        return self.token_issuer_configured and all(
            self._has_value(value)
            for value in (
                self.google_application_credentials,
                # Google TTS uses same credentials as STT/Gemini
            )
        )

    def require_token_issuer(self) -> None:
        self._require("LIVEKIT_URL", self.livekit_url)
        self._require("LIVEKIT_API_KEY", self.livekit_api_key)
        self._require("LIVEKIT_API_SECRET", self.livekit_api_secret)

    def require_agent_providers(self) -> None:
        self.require_token_issuer()
        self._require("GOOGLE_APPLICATION_CREDENTIALS", self.google_application_credentials)

    @property
    def qdrant_configured(self) -> bool:
        return bool(self.qdrant_url.strip())

    def require_knowledge_retrieval(self) -> None:
        self._require("QDRANT_URL", self.qdrant_url)
        self._require("GOOGLE_APPLICATION_CREDENTIALS", self.google_application_credentials)

    @staticmethod
    def _require(name: str, value: str | SecretStr | None) -> None:
        if not Settings._has_value(value):
            raise MissingConfigurationError(f"{name} must be configured on the server.")

    @staticmethod
    def _has_value(value: str | SecretStr | None) -> bool:
        if value is None:
            return False
        if isinstance(value, SecretStr):
            return bool(value.get_secret_value().strip())
        return bool(value.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a single immutable-ish settings instance per process."""

    settings = Settings()
    # Keep a private development signing key stable across FastAPI reloads.
    # A process-local random key would invalidate every browser session when
    # the reloader restarts the server after an ordinary code change.
    if not settings.is_production and (
        settings.jwt_secret_key is None or not settings.jwt_secret_key.get_secret_value().strip()
    ):
        settings.jwt_secret_key = SecretStr(_load_or_create_development_jwt_secret())
    return settings


def _load_or_create_development_jwt_secret() -> str:
    """Return a Git-ignored, per-workspace signing key for local development."""

    secret_file = Path(__file__).resolve().parents[2] / ".sahayak-dev-jwt"
    try:
        existing = secret_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass

    generated = secrets.token_urlsafe(48)
    try:
        # Exclusive creation prevents a Uvicorn reloader parent and child from
        # replacing one another's development session key.
        with secret_file.open("x", encoding="utf-8") as file:
            file.write(generated)
        return generated
    except FileExistsError:
        existing = secret_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except OSError as error:
        raise MissingConfigurationError(
            "JWT_SECRET_KEY must be configured when the development key cannot be stored."
        ) from error

    raise MissingConfigurationError("Development JWT secret could not be initialized.")
