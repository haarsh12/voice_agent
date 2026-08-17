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

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    livekit_url: str = ""
    livekit_api_key: SecretStr | None = None
    livekit_api_secret: SecretStr | None = None
    agent_name: str = "vyamit-voice"

    # Google Cloud STT configuration
    google_application_credentials: str | None = None
    google_stt_language: str = "hi-IN"  # Default to Hindi with multi-language support
    google_stt_model: str = "latest_long"
    google_keyterms: str = "Vyamit,व्यामित,नमस्ते,धन्यवाद,मराठी"

    # Gemini runs through Vertex AI using GOOGLE_APPLICATION_CREDENTIALS. The
    # project can be inferred from a service-account key, but specifying it is
    # useful for workload identity and other non-key credential sources.
    google_cloud_project: str = ""
    google_cloud_location: str = "global"
    gemini_model: str = "gemini-3.5-flash"
    gemini_temperature: float = Field(default=0.35, ge=0, le=2)

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
                self.cartesia_api_key,
            )
        )

    def require_token_issuer(self) -> None:
        self._require("LIVEKIT_URL", self.livekit_url)
        self._require("LIVEKIT_API_KEY", self.livekit_api_key)
        self._require("LIVEKIT_API_SECRET", self.livekit_api_secret)

    def require_agent_providers(self) -> None:
        self.require_token_issuer()
        self._require("GOOGLE_APPLICATION_CREDENTIALS", self.google_application_credentials)
        self._require("CARTESIA_API_KEY", self.cartesia_api_key)

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
