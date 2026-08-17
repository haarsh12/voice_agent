#!/usr/bin/env python3
"""Make one real Gemini request through Vertex AI using the configured service account."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from google.genai.types import AutomaticFunctionCallingConfig, GenerateContentConfig

_BACKEND_DIRECTORY = Path(__file__).resolve().parent
_PROJECT_DIRECTORY = _BACKEND_DIRECTORY.parent

# Mirror the environment loading order used by the LiveKit agent.
load_dotenv(_PROJECT_DIRECTORY / ".env")
load_dotenv(_PROJECT_DIRECTORY / ".env.local", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env", override=True)
load_dotenv(_BACKEND_DIRECTORY / ".env.local", override=True)

from app.config.settings import get_settings
from app.services.gemini import create_gemini_client, load_vertex_authentication


def _explain_failure(error: Exception) -> str:
    message = str(error).lower()
    if "permission_denied" in message or "403" in message:
        return "Check that the service account has the Vertex AI User role (roles/aiplatform.user)."
    if "not_found" in message or "404" in message:
        return "Check GEMINI_MODEL and GOOGLE_CLOUD_LOCATION; do not use retired gemini-1.5 models."
    if "quota" in message or "429" in message:
        return "The model is reachable, but the project needs available Gemini quota."
    return "See the exception above; credential, billing, and Vertex AI API setup are the relevant checks."


def main() -> int:
    settings = get_settings()
    try:
        auth = load_vertex_authentication(settings)
        client = create_gemini_client(settings)
        print("Gemini Vertex AI test")
        print(f"Project: {auth.project_id}")
        print(f"Location: {settings.google_cloud_location}")
        print(f"Model: {settings.gemini_model}")

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents="Reply with exactly: Vertex AI connectivity verified.",
            config=GenerateContentConfig(
                automatic_function_calling=AutomaticFunctionCallingConfig(disable=True)
            ),
        )
        text = (response.text or "").strip()
        if not text:
            print("FAIL: Gemini returned no text.")
            return 1

        print(f"PASS: {text}")
        return 0
    except Exception as error:
        print(f"FAIL: {error}")
        print(f"Hint: {_explain_failure(error)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
