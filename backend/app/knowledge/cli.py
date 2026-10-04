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
from app.schemes.repository import SchemeRepository


async def _run(
    source_key: str | None,
    *,
    reconcile: bool = False,
    reindex_source: str | None = None,
    backfill_schemes: bool = False,
    ingest_all: bool = False,
    force_check: bool = False,
) -> int:
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
        if reconcile:
            await service.repository.sync_source_registry()
            report = await service.reconcile_current_vectors()
            logging.info(
                "knowledge_vector_reconciliation_complete current=%s repaired=%s retired=%s",
                report.current_records,
                report.repaired_missing,
                report.retired_stale,
            )
        elif reindex_source:
            await service.repository.sync_source_registry()
            count = await service.reindex_current_source(reindex_source)
            logging.info("knowledge_source_reindex_complete source=%s chunks=%s", reindex_source, count)
        elif backfill_schemes:
            # Reuses only durable CURRENT documents already accepted by the
            # knowledge pipeline.  It makes no network request and does not
            # invent records, so it is safe to run after a deployment.
            count = await SchemeRepository(session).sync_current_documents()
            logging.info("scheme_catalog_backfill_complete changed=%s", count)
        elif ingest_all:
            # Force check all registered sources regardless of check_interval
            await service.repository.sync_source_registry()
            recovered = await service.repository.recover_interrupted_checks()
            if recovered:
                logging.warning("knowledge_interrupted_checks_recovered count=%s", recovered)
            
            total_sources = len(SOURCES_BY_KEY)
            successful = 0
            failed = 0
            unchanged = 0
            changed = 0
            
            logging.info("knowledge_bulk_ingestion_started total_sources=%s force=%s", total_sources, force_check)
            
            for idx, (key, source) in enumerate(sorted(SOURCES_BY_KEY.items()), 1):
                if not source.enabled:
                    logging.info("knowledge_source_skipped source=%s reason=disabled progress=%s/%s", key, idx, total_sources)
                    continue
                    
                logging.info("knowledge_source_checking source=%s progress=%s/%s", key, idx, total_sources)
                try:
                    result = await service.check_source(source)
                    if result.value == "FAILED":
                        failed += 1
                        logging.warning("knowledge_source_failed source=%s result=%s", key, result.value)
                    elif result.value == "UNCHANGED":
                        unchanged += 1
                        logging.info("knowledge_source_unchanged source=%s", key)
                    elif result.value in {"CHANGED", "PARTIAL_FAILURE"}:
                        changed += 1
                        successful += 1
                        logging.info("knowledge_source_completed source=%s result=%s", key, result.value)
                    else:
                        successful += 1
                        logging.info("knowledge_source_completed source=%s result=%s", key, result.value)
                except Exception as error:
                    failed += 1
                    await session.rollback()
                    logging.error("knowledge_source_exception source=%s error=%s", key, str(error), exc_info=True)
            
            logging.info(
                "knowledge_bulk_ingestion_complete total=%s successful=%s failed=%s unchanged=%s changed=%s",
                total_sources, successful, failed, unchanged, changed
            )
            
            # After bulk ingestion, backfill schemes from all newly ingested documents
            try:
                scheme_count = await SchemeRepository(session).sync_current_documents()
                logging.info("scheme_catalog_backfill_complete changed=%s", scheme_count)
            except Exception as error:
                logging.error("scheme_catalog_backfill_failed error=%s", str(error), exc_info=True)
                
        elif source_key:
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--reconcile", action="store_true", help="Repair missing/stale Qdrant CURRENT points from the audit store.")
    group.add_argument("--reindex-source", choices=sorted(SOURCES_BY_KEY), help="Force one reviewed source's CURRENT chunks back into Qdrant.")
    group.add_argument("--backfill-schemes", action="store_true", help="Build scheme records from already-ingested approved documents.")
    group.add_argument("--ingest-all", action="store_true", help="Force ingestion of ALL registered sources (ignores check intervals).")
    parser.add_argument("--force", action="store_true", help="Force check even if interval hasn't elapsed (use with --source or --ingest-all).")
    arguments = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            _run(
                arguments.source,
                reconcile=arguments.reconcile,
                reindex_source=arguments.reindex_source,
                backfill_schemes=arguments.backfill_schemes,
                ingest_all=arguments.ingest_all,
                force_check=arguments.force,
            )
        )
    )


if __name__ == "__main__":
    main()
