from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.config.settings import Settings, get_settings
from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            livekit_url="wss://example.livekit.cloud",
            livekit_api_key="test-key",
            livekit_api_secret="test-secret",
            google_application_credentials="service-account.json",
            cartesia_api_key="cartesia",
        )
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_health_reports_the_configured_agent(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "agent_name": "vyamit-voice", "configured": True},
        )

    def test_token_endpoint_uses_current_token_source_payload(self) -> None:
        response = self.client.post(
            "/api/token",
            json={"room_name": "voice-test", "participant_name": "Guest"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"server_url", "participant_token"})
        self.assertEqual(body["server_url"], "wss://example.livekit.cloud")
        self.assertTrue(body["participant_token"])
