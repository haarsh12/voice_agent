"""Offline, incremental ingestion of reviewed source documents."""

from __future__ import annotations

import asyncio
import logging
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
from app.knowledge.vectors import QdrantVectorStore, VectorRecord, VectorStoreError, VertexEmbeddingProvider

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

    async def check_due_sources(self) -> dict[str, SourceCheckResult]:
        """Seed the registry, then process only sources whose configured interval is due."""

        await self.repository.sync_source_registry()
        results: dict[str, SourceCheckResult] = {}
        for source in await self.repository.due_sources():
            definition = SOURCES_BY_KEY.get(source.key)
            if definition is None:
                continue
            results[source.key] = await self.check_source(definition)
        return results

    async def check_source(self, source: ApprovedSourceDefinition) -> SourceCheckResult:
        """Check a finite source set, preserving previous current versions on failure."""

        check = await self.repository.create_check(source.key)
        # Persist the audit row first so one failed document can be rolled back
        # without accidentally committing a partial version on a later URL.
        await self.repository.session.commit()
        checked = 0
        changed = 0
        failures = 0
        try:
            for url in self.adapter.documents_to_check(source):
                checked += 1
                try:
                    was_changed = await self._check_document(source, url)
                except (SourceFetchError, SourceExtractionError, VectorStoreError, ValueError):
                    await self.repository.session.rollback()
                    failures += 1
                    continue
                changed += int(was_changed)
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
            SourceCheckResult.PARTIAL_FAILURE
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

    async def _check_document(self, source: ApprovedSourceDefinition, url: str) -> bool:
        """Fetch → compare hash → extract → chunk → embed → index one source document."""

        latest = await self.repository.latest_version(source_key=source.key, canonical_url=url)
        headers = conditional_request_headers(
            etag=latest.source_metadata.get("etag") if latest else None,
            last_modified=latest.source_metadata.get("last_modified") if latest else None,
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
            return False

        extracted = extract_source_document(fetched)
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
            return False

        chunks = chunk_semantically(extracted.text)
        if not chunks:
            raise SourceExtractionError("approved source did not contain indexable semantic chunks")
        stored_chunks = await self.repository.add_chunks(
            document_version_id=version.id,
            chunks=[
                {
                    "heading": chunk.heading,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "language": None,
                }
                for chunk in chunks
            ],
        )
        vectors = await asyncio.to_thread(self.embedding_provider.embed, [chunk.content for chunk in stored_chunks])
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
        return True
