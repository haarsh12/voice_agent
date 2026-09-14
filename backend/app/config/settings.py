"""Typed, environment-only configuration for the API and voice agent."""

from __future__ import annotations

from functools import lru_cache

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
    jwt_access_token_minutes: int = Field(default=60 * 24 * 7, ge=5, le=60 * 24 * 30)
    otp_demo_mode: bool = True
    otp_demo_code: SecretStr | None = None
    fast2sms_api_key: SecretStr | None = None
    fast2sms_base_url: str = "https://www.fast2sms.com/dev/bulkV2"

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
            r"localhost|127\\.0\\.0\\.1|\\[::1\\]|"
            r"10(?:\\.\\d{1,3}){3}|"
            r"192\\.168(?:\\.\\d{1,3}){2}|"
            r"172\\.(?:1[6-9]|2\\d|3[0-1])(?:\\.\\d{1,3}){2}"
            r")(?::\\d{1,5})?$"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def async_database_url(self) -> str | None:
        if self.database_url is None:
            return None
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
        if self.otp_demo_mode:
            raise MissingConfigurationError("OTP_DEMO_MODE must be disabled in production.")
        if not self.allowed_origins or any(not origin.startswith("https://") for origin in self.allowed_origins):
            raise MissingConfigurationError("CORS_ORIGINS must contain explicit HTTPS origins in production.")

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

    return Settings()
