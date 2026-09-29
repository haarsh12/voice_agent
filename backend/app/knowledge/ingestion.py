"""Offline, incremental ingestion of reviewed source documents."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.knowledge.adapters import DEFAULT_SOURCE_ADAPTER, SourceAdapter
from app.knowledge.chunking import chunk_semantically
from app.knowledge.contracts import DocumentStatus, SourceCheckResult
from app.knowledge.extraction import SourceExtractionError, extract_source_document
from app.knowledge.fetching import (
    SourceFetchError,
    conditional_request_headers,
    fetch_approved_document,
    parse_http_date,
)
from app.knowledge.registry import SOURCES_BY_KEY, ApprovedSourceDefinition
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.ocr import OcrProvider, create_ocr_provider
from app.knowledge.vectors import (
    EmbeddingError,
    QdrantVectorStore,
    VectorRecord,
    VectorStoreError,
    VertexEmbeddingProvider,
)

logger = logging.getLogger("sahayak.knowledge.ingestion")


class KnowledgeIngestionService:
    """Runs outside the user request path and processes only changed content."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        adapter: SourceAdapter = DEFAULT_SOURCE_ADAPTER,
    ) -> None:
        self.repository = KnowledgeRepository(session)
        self.settings = settings
        self.adapter = adapter
        self.vector_store = QdrantVectorStore(settings)
        self.embedding_provider = VertexEmbeddingProvider(settings)
        self.ocr_provider: OcrProvider | None = create_ocr_provider(settings)

    async def check_due_sources(self) -> dict[str, SourceCheckResult]:
        """Seed the registry, then process only sources whose configured interval is due."""

        await self.repository.sync_source_registry()
        recovered = await self.repository.recover_interrupted_checks()
        if recovered:
            logger.warning("knowledge_interrupted_checks_recovered count=%s", recovered)
        results: dict[str, SourceCheckResult] = {}
        # ``check_source`` may roll back after one failed document. Hold plain
        # keys rather than ORM objects so an expired row cannot trigger an
        # implicit async reload while the remaining sources are processed.
        source_keys = [source.key for source in await self.repository.due_sources()]
        for source_key in source_keys:
            definition = SOURCES_BY_KEY.get(source_key)
            if definition is None:
                continue
            results[source_key] = await self.check_source(definition)
        return results

    async def check_source(self, source: ApprovedSourceDefinition) -> SourceCheckResult:
        """Check a finite source set, preserving previous current versions on failure."""

        check = await self.repository.create_check(source.key)
        if check is None:
            logger.info("knowledge_source_check_skipped source=%s reason=already_running", source.key)
            return SourceCheckResult.UNCHANGED
        # Persist the audit row first so one failed document can be rolled back
        # without accidentally committing a partial version on a later URL.
        await self.repository.session.commit()
        checked = 0
        changed = 0
        failures = 0
        try:
            entry_urls = {url for url in self.adapter.documents_to_check(source)}
            pending_urls = deque(entry_urls)
            seen_urls: set[str] = set()
            while pending_urls and checked < source.max_documents_per_check:
                url = pending_urls.popleft()
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                checked += 1
                try:
                    was_changed, discovered_urls = await self._check_document(
                        source,
                        url,
                        discover=url in entry_urls,
                        force_discovery_refresh=url in entry_urls,
                    )
                except (EmbeddingError, SourceFetchError, SourceExtractionError, VectorStoreError, ValueError) as error:
                    await self.repository.session.rollback()
                    failures += 1
                    logger.warning(
                        "knowledge_document_check_failed source=%s reason=%s",
                        source.key,
                        str(error) or type(error).__name__,
                    )
                    continue
                changed += int(was_changed)
                for discovered_url in discovered_urls:
                    if discovered_url not in seen_urls:
                        pending_urls.append(discovered_url)
        except Exception:
            # An unexpected worker failure still leaves prior CURRENT versions
            # intact; browser queries will never get an invented fallback.
            await self.repository.session.rollback()
            await self.repository.finish_check(
                check,
                result=SourceCheckResult.FAILED,
                checked_documents=checked,
                changed_documents=changed,
                failure_code="unexpected_worker_failure",
            )
            return SourceCheckResult.FAILED

        result = (
            # If no document in a source group could be checked, do not leave
            # it marked APPROVED. The next scheduler invocation will retry it
            # and retrieval continues to exclude the source meanwhile.
            SourceCheckResult.FAILED
            if checked and failures == checked
            else SourceCheckResult.PARTIAL_FAILURE
            if failures
            else SourceCheckResult.CHANGED
            if changed
            else SourceCheckResult.UNCHANGED
        )
        await self.repository.finish_check(
            check,
            result=result,
            checked_documents=checked,
            changed_documents=changed,
            failure_code="source_document_failure" if failures else None,
        )
        logger.info(
            "knowledge_source_check_complete source=%s result=%s checked=%s changed=%s failures=%s",
            source.key,
            result.value,
            checked,
            changed,
            failures,
        )
        return result

    async def _check_document(
        self,
        source: ApprovedSourceDefinition,
        url: str,
        *,
        discover: bool,
        force_discovery_refresh: bool,
    ) -> tuple[bool, tuple[str, ...]]:
        """Fetch → compare hash → extract → chunk → embed → index one source document."""

        latest = await self.repository.latest_version(source_key=source.key, canonical_url=url)
        # Entry pages are fetched afresh so their approved one-hop links can
        # rebuild the bounded queue after a worker restart. The page itself is
        # still hash-compared and never re-embedded unless its bytes changed.
        headers = (
            {}
            if force_discovery_refresh
            else conditional_request_headers(
                etag=latest.source_metadata.get("etag") if latest else None,
                last_modified=latest.source_metadata.get("last_modified") if latest else None,
            )
        )
        fetched = await fetch_approved_document(
            url=url,
            source=source,
            settings=self.settings,
            conditional_headers=headers,
        )
        if fetched is None:
            if latest is not None:
                latest.last_checked_at = datetime.now(UTC)
                await self.repository.session.commit()
            return False, ()

        discovered_urls = (
            self.adapter.discover_documents(
                source=source,
                entry_url=fetched.canonical_url,
                content=fetched.content,
                content_type=fetched.content_type,
            )
            if discover
            else ()
        )

        try:
            extracted = await asyncio.wait_for(
                asyncio.to_thread(
                    extract_source_document,
                    fetched,
                    ocr_provider=self.ocr_provider,
                    max_pdf_pages=self.settings.knowledge_pdf_max_pages,
                ),
                timeout=self.settings.knowledge_document_processing_timeout_seconds,
            )
        except TimeoutError as error:
            raise SourceExtractionError("source_extraction_timed_out") from error
        metadata = {
            "etag": fetched.etag or "",
            "last_modified": fetched.last_modified or "",
            "content_type": fetched.content_type,
        }
        previous_point_ids = (
            await self.repository.current_vector_point_ids(
                source_key=source.key,
                canonical_url=fetched.canonical_url,
            )
            if latest is not None and latest.content_hash != fetched.content_hash
            else []
        )
        version, changed = await self.repository.record_document_version(
            source_key=source.key,
            canonical_url=fetched.canonical_url,
            source_url=fetched.url,
            title=extracted.title,
            content_hash=fetched.content_hash,
            extraction_method=extracted.extraction_method,
            is_ocr=extracted.is_ocr,
            ocr_confidence=extracted.ocr_confidence,
            source_metadata=metadata,
            last_modified_at=parse_http_date(fetched.last_modified),
        )
        if not changed:
            await self.repository.session.commit()
            return False, discovered_urls

        try:
            chunks = await asyncio.wait_for(
                asyncio.to_thread(chunk_semantically, extracted.text),
                timeout=self.settings.knowledge_document_processing_timeout_seconds,
            )
        except TimeoutError as error:
            raise SourceExtractionError("source_chunking_timed_out") from error
        if not chunks:
            raise SourceExtractionError("approved source did not contain indexable semantic chunks")
        stored_chunks = await self.repository.add_chunks(
            document_version_id=version.id,
            chunks=[
                {
                    "heading": chunk.heading,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "page_number": chunk.page_number,
                    "language": None,
                }
                for chunk in chunks
            ],
        )
        try:
            vectors = await asyncio.wait_for(
                asyncio.to_thread(self.embedding_provider.embed, [chunk.content for chunk in stored_chunks]),
                timeout=self.settings.knowledge_document_processing_timeout_seconds,
            )
        except TimeoutError as error:
            raise EmbeddingError("embedding_generation_timed_out") from error
        if len(vectors) != len(stored_chunks):
            raise VectorStoreError("embedding_chunk_count_mismatch")
        await asyncio.to_thread(self.vector_store.ensure_collection)
        # Index the replacement before retiring an old Qdrant payload. Qdrant
        # and PostgreSQL cannot share one transaction, so this ordering means
        # an indexing failure leaves the old CURRENT database/version path
        # intact. The relational retrieval check remains the authority.
        await asyncio.to_thread(
            self.vector_store.upsert,
            [
                VectorRecord(
                    point_id=chunk.vector_point_id,
                    vector=vector,
                    payload={
                        "source_key": source.key,
                        "document_version_id": version.id,
                        "document_status": DocumentStatus.CURRENT.value,
                        "state": chunk.state or "",
                        "district": chunk.district or "",
                        "language": chunk.language or "",
                        "scheme_key": chunk.scheme_key or "",
                    },
                )
                for chunk, vector in zip(stored_chunks, vectors, strict=True)
            ],
        )
        await self.repository.session.commit()
        if previous_point_ids:
            try:
                await asyncio.to_thread(
                    self.vector_store.set_document_status,
                    previous_point_ids,
                    DocumentStatus.SUPERSEDED.value,
                )
            except VectorStoreError:
                # The new CURRENT version is already durable and retrieval
                # validates all hits against it relationally. Keeping an older
                # point searchable for one check cycle is safe; it cannot be
                # cited because its version is SUPERSEDED in PostgreSQL.
                logger.warning("knowledge_vector_status_sync_deferred source=%s", source.key)
                pass
        return True, discovered_urls
