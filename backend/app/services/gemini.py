"""Shared, supported Gemini-on-Vertex AI client setup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from google.auth.credentials import Credentials
from google.genai import Client
from google.genai.types import HttpOptions
from google.oauth2 import service_account

from app.config.settings import MissingConfigurationError, Settings

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


@dataclass(frozen=True)
class VertexAuthentication:
    """The resolved project and scoped credentials for Vertex AI."""

    credentials: Credentials
    project_id: str


def load_vertex_authentication(settings: Settings) -> VertexAuthentication:
    """Load the configured service account and infer its project when needed."""

    credentials_path = settings.google_application_credentials
    if not credentials_path:
        raise MissingConfigurationError(
            "GOOGLE_APPLICATION_CREDENTIALS must be configured on the server."
        )

    credential_file = Path(credentials_path).expanduser()
    if not credential_file.is_file():
        raise MissingConfigurationError(
            "GOOGLE_APPLICATION_CREDENTIALS does not point to a credential file."
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(credential_file), scopes=[_CLOUD_PLATFORM_SCOPE]
    )
    project_id = settings.google_cloud_project or credentials.project_id
    if not project_id:
        raise MissingConfigurationError(
            "GOOGLE_CLOUD_PROJECT must be configured when the credential file has no project ID."
        )

    return VertexAuthentication(credentials=credentials, project_id=project_id)


def create_gemini_client(settings: Settings) -> Client:
    """Create the stable v1 Gemini API client backed by Vertex AI."""

    auth = load_vertex_authentication(settings)
    return Client(
        vertexai=True,
        project=auth.project_id,
        location=settings.google_cloud_location,
        credentials=auth.credentials,
        http_options=HttpOptions(api_version="v1"),
    )
