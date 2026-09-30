"""Offline, incremental ingestion of reviewed source documents."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
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
from app.schemes.repository import SchemeRepository
from app.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion, KnowledgeSource
from app.knowledge.ocr import OcrProvider, create_ocr_provider
from app.knowledge.vectors import (
    EmbeddingError,
    QdrantVectorStore,
    VectorRecord,
    VectorStoreError,
    VertexEmbeddingProvider,
)

logger = logging.getLogger("sahayak.knowledge.ingestion")


@dataclass(frozen=True)
class VectorConsistencyReport:
    """Counts from a Qdrant repair run; no source content is logged or returned."""

    current_records: int
    repaired_missing: int
    retired_stale: int


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
            entry_urls = self.adapter.documents_to_check(source)
            # Each discovered document inherits only the categories from its
            # reviewed parent target. We never infer coverage from model text
            # or a URL keyword, so a successful generic homepage check cannot
            # make PMFBY claims or legal coverage appear complete.
            pending_urls = deque(
                (url, source.categories_for_entry_url(url)) for url in entry_urls
            )
            seen_urls: set[str] = set()
            while pending_urls and checked < source.max_documents_per_check:
                url, coverage_categories = pending_urls.popleft()
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
                        coverage_categories=coverage_categories,
                    )
                except (EmbeddingError, SourceFetchError, SourceExtractionError, VectorStoreError, ValueError) as error:
                    await self.repository.session.rollback()
                    failures += 1
                    await self.repository.record_resource_failure(
                        source_key=source.key,
                        canonical_url=url,
                        failure_code=str(error) or type(error).__name__,
                    )
                    logger.warning(
                        "knowledge_document_check_failed source=%s reason=%s",
                        source.key,
                        str(error) or type(error).__name__,
                    )
                    continue
                changed += int(was_changed)
                for discovered_url in discovered_urls:
                    if discovered_url not in seen_urls:
                        pending_urls.append((discovered_url, coverage_categories))
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

    async def reconcile_current_vectors(self, *, source_key: str | None = None) -> VectorConsistencyReport:
        """Repair only missing/stale Qdrant points from the durable CURRENT corpus.

        The job is deliberately explicit (CLI-triggered), not part of a user
        request or chat turn. It makes a derived vector index converge without
        replacing relational audit history or fetching arbitrary content.
        """

        rows = await self.repository.current_chunks_for_reindex(source_key=source_key)
        expected_ids = {chunk.vector_point_id for chunk, _version, _document, _source in rows}
        filters = {"document_status": DocumentStatus.CURRENT.value}
        if source_key is not None:
            filters["source_key"] = source_key
        await asyncio.to_thread(self.vector_store.ensure_collection)
        indexed_ids = await asyncio.to_thread(self.vector_store.existing_point_ids, filters=filters)
        missing_rows = [row for row in rows if row[0].vector_point_id not in indexed_ids]
        stale_ids = sorted(indexed_ids - expected_ids)
        if missing_rows:
            vectors = await asyncio.to_thread(
                self.embedding_provider.embed,
                [chunk.content for chunk, _version, _document, _source in missing_rows],
            )
            if len(vectors) != len(missing_rows):
                raise VectorStoreError("embedding_chunk_count_mismatch")
            await asyncio.to_thread(
                self.vector_store.upsert,
                [
                    self._vector_record(chunk, version, document, source, vector)
                    for (chunk, version, document, source), vector in zip(missing_rows, vectors, strict=True)
                ],
            )
        if stale_ids:
            await asyncio.to_thread(
                self.vector_store.set_document_status,
                stale_ids,
                DocumentStatus.SUPERSEDED.value,
            )
        report = VectorConsistencyReport(
            current_records=len(rows),
            repaired_missing=len(missing_rows),
            retired_stale=len(stale_ids),
        )
        logger.info(
            "knowledge_vector_reconciled source=%s current=%s repaired=%s retired=%s",
            source_key or "all",
            report.current_records,
            report.repaired_missing,
            report.retired_stale,
        )
        return report

    async def reindex_current_source(self, source_key: str) -> int:
        """Force a reviewed source's CURRENT chunks back into Qdrant.

        This is a controlled recovery operation for an embedding-model change
        or a confirmed Qdrant data-loss event. It never deletes source
        versions and it reuses only already-approved, extracted text.
        """

        rows = await self.repository.current_chunks_for_reindex(source_key=source_key)
        if not rows:
            return 0
        vectors = await asyncio.to_thread(
            self.embedding_provider.embed,
            [chunk.content for chunk, _version, _document, _source in rows],
        )
        if len(vectors) != len(rows):
            raise VectorStoreError("embedding_chunk_count_mismatch")
        await asyncio.to_thread(self.vector_store.ensure_collection)
        await asyncio.to_thread(
            self.vector_store.upsert,
            [
                self._vector_record(chunk, version, document, source, vector)
                for (chunk, version, document, source), vector in zip(rows, vectors, strict=True)
            ],
        )
        logger.info("knowledge_source_reindexed source=%s chunks=%s", source_key, len(rows))
        return len(rows)

    async def _check_document(
        self,
        source: ApprovedSourceDefinition,
        url: str,
        *,
        discover: bool,
        force_discovery_refresh: bool,
        coverage_categories: tuple[str, ...],
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
                await self.repository.resolve_resource_failure(
                    source_key=source.key,
                    canonical_url=url,
                )
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
            coverage_categories=coverage_categories,
            last_modified_at=parse_http_date(fetched.last_modified),
        )
        if not changed:
            await self.repository.session.commit()
            await self.repository.resolve_resource_failure(
                source_key=source.key,
                canonical_url=fetched.canonical_url,
            )
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
        # Build/update the canonical scheme catalogue from the very same
        # approved document version and chunks.  This stays inside the
        # ingestion transaction: a failed extraction or vector write cannot
        # expose a partial, browser-visible scheme record.
        await SchemeRepository(self.repository.session).upsert_from_document(
            source=await self.repository.session.get(KnowledgeSource, source.key) or source,
            version=version,
            chunks=stored_chunks,
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
                self._vector_record(chunk, version, None, source, vector)
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
        await self.repository.resolve_resource_failure(
            source_key=source.key,
            canonical_url=fetched.canonical_url,
        )
        return True, discovered_urls

    @staticmethod
    def _vector_record(
        chunk: KnowledgeChunk,
        version: KnowledgeDocumentVersion,
        document: KnowledgeDocument | None,
        source: KnowledgeSource | ApprovedSourceDefinition,
        vector: list[float],
    ) -> VectorRecord:
        """Build one stable Qdrant payload from audited relational metadata."""

        # These objects are ORM instances at every call site. Keeping this
        # helper local prevents duplicate payload contracts between normal
        # ingestion, missing-point repair, and explicit reindexing.
        del document
        return VectorRecord(
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
                "source_authority": source.authority_level,
                "coverage_categories": list(version.coverage_categories),
                "document_type": source.category,
                "chunk_type": chunk.heading or "content",
            },
        )
