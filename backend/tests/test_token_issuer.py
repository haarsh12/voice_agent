from __future__ import annotations

import unittest

from livekit import api

from app.config.settings import Settings
from app.services.token_issuer import issue_browser_token


class TokenIssuerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            livekit_url="wss://example.livekit.cloud",
            livekit_api_key="test-key",
            livekit_api_secret="test-secret",
        )

    def test_issued_token_is_limited_to_the_requested_room_and_agent(self) -> None:
        issued = issue_browser_token(
            self.settings,
            room_name="vyamit-test",
            participant_name="Test user",
            participant_identity="test-user",
        )

        claims = api.TokenVerifier("test-key", "test-secret").verify(
            issued.participant_token
        )
        self.assertEqual(issued.server_url, "wss://example.livekit.cloud")
        self.assertTrue(claims.video.room_join)
        self.assertEqual(claims.video.room, "vyamit-test")
        self.assertEqual(claims.room_config.agents[0].agent_name, "vyamit-voice")
