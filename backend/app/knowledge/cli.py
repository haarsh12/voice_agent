"""Operational entry point for the separate knowledge-source check worker.

Run this command from a scheduler (cron, a managed job, or a worker service),
not from a FastAPI request. The source registry decides which checks are due.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from app.auth.session import ensure_development_auth_schema, get_engine, get_session_factory
from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.knowledge.ingestion import KnowledgeIngestionService
from app.knowledge.registry import SOURCES_BY_KEY


async def _run(source_key: str | None) -> int:
    settings = get_settings()
    session_factory = get_session_factory()
    engine = get_engine()
    if session_factory is None or engine is None:
        logging.error("knowledge_worker_database_unavailable")
        return 2
    if (
        not settings.is_production
        and settings.async_database_url
        and settings.async_database_url.startswith("sqlite")
    ):
        await ensure_development_auth_schema(engine)
    async with session_factory() as session:
        service = KnowledgeIngestionService(session, settings)
        if source_key:
            await service.repository.sync_source_registry()
            recovered = await service.repository.recover_interrupted_checks()
            if recovered:
                logging.warning("knowledge_interrupted_checks_recovered count=%s", recovered)
            source = SOURCES_BY_KEY.get(source_key)
            if source is None:
                logging.error("knowledge_worker_unknown_source")
                return 2
            result = await service.check_source(source)
            logging.info("knowledge_source_check_complete result=%s", result.value)
        else:
            results = await service.check_due_sources()
            logging.info("knowledge_due_checks_complete sources=%s", len(results))
    return 0


def main() -> None:
    configure_logging()
    # HTTP libraries otherwise log every official URL and cloud request at INFO.
    # Worker telemetry records source keys and outcome counts without turning
    # operational logs into a document catalogue.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Run due Sahayak verified-knowledge source checks.")
    parser.add_argument("--source", choices=sorted(SOURCES_BY_KEY), help="Check one reviewed source immediately.")
    arguments = parser.parse_args()
    raise SystemExit(asyncio.run(_run(arguments.source)))


if __name__ == "__main__":
    main()
