"""Consistent, secret-safe application logging."""

from __future__ import annotations

import logging


def configure_logging() -> None:
    """Configure concise logs once without changing third-party logger levels."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
