from __future__ import annotations

import unittest

from app.config.settings import MissingConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def test_empty_secret_is_not_considered_configured(self) -> None:
        settings = Settings(
            livekit_url="wss://example.livekit.cloud",
            livekit_api_key="",
            livekit_api_secret="",
        )

        self.assertFalse(settings.token_issuer_configured)
        with self.assertRaises(MissingConfigurationError):
            settings.require_token_issuer()

    def test_all_provider_credentials_enable_agent_configuration(self) -> None:
        settings = Settings(
            livekit_url="wss://example.livekit.cloud",
            livekit_api_key="key",
            livekit_api_secret="secret",
            google_application_credentials="service-account.json",
            cartesia_api_key="cartesia",
            google_keyterms="Vyamit",
        )

        self.assertTrue(settings.agent_providers_configured)
        self.assertEqual(settings.keyterms, ["Vyamit"])
