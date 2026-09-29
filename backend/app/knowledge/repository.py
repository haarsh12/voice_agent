"""Database operations for the verified knowledge lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Select, func, inspect, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.contracts import DocumentStatus, SourceCheckResult, SourceValidationStatus
from app.knowledge.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeSource,
    KnowledgeSourceCheck,
)
from app.knowledge.registry import SOURCE_REGISTRY, ApprovedSourceDefinition


def utc_now() -> datetime:
    return datetime.now(UTC)


class KnowledgeRepository:
    """Canonical relational store; all ingestion writes flow through this class."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sync_source_registry(self) -> None:
        """Create or update only the reviewed configuration fields for the 10 sources."""

        for definition in SOURCE_REGISTRY:
            source = await self.session.get(KnowledgeSource, definition.key)
            values = _source_values(definition)
            if source is None:
                self.session.add(KnowledgeSource(**values))
            else:
                for field, value in values.items():
                    # Runtime operational state belongs to the check worker,
                    # not a static registry sync. In particular, do not turn
                    # a CHECK_FAILED source back into APPROVED until a real
                    # successful source check has completed.
                    if field not in {"key", "enabled", "validation_status"}:
                        setattr(source, field, value)
        await self.session.commit()

    async def due_sources(self, *, now: datetime | None = None) -> list[KnowledgeSource]:
        """Select enabled sources whose independent registry interval has elapsed."""

        now = now or utc_now()
        sources = list((await self.session.scalars(select(KnowledgeSource).where(KnowledgeSource.enabled.is_(True)))).all())
        return [
            source
            for source in sources
            if source.validation_status != SourceValidationStatus.APPROVED.value
            or source.last_successful_check_at is None
            or _as_utc(source.last_successful_check_at) + timedelta(hours=source.check_interval_hours) <= now
        ]

    async def create_check(self, source_key: str, *, started_at: datetime | None = None) -> KnowledgeSourceCheck | None:
        """Create a source check, or return ``None`` if another worker owns it."""

        check = KnowledgeSourceCheck(
            id=str(uuid4()),
            source_key=source_key,
            started_at=started_at or utc_now(),
            result=SourceCheckResult.UNCHANGED.value,
        )
        self.session.add(check)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            return None
        return check

    async def recover_interrupted_checks(
        self,
        *,
        stale_after: timedelta = timedelta(minutes=15),
    ) -> int:
        """Close abandoned worker audit rows before a new scheduled run begins.

        A process can be restarted by a scheduler, deployment rollout, or host
        failure after it created a check row. Leaving that row open makes the
        audit trail misleading. Only rows older than the grace period are
        recovered; a second live worker must be rejected by the unique open
        check constraint rather than being allowed to cancel the first worker.
        """

        cutoff = utc_now() - stale_after
        unfinished = list(
            (
                await self.session.scalars(
                    select(KnowledgeSourceCheck).where(
                        KnowledgeSourceCheck.completed_at.is_(None),
                        KnowledgeSourceCheck.started_at <= cutoff,
                    )
                )
            ).all()
        )
        if not unfinished:
            return 0
        now = utc_now()
        for check in unfinished:
            check.completed_at = now
            check.result = SourceCheckResult.FAILED.value
            check.failure_code = "interrupted_worker"
            source = await self.session.get(KnowledgeSource, check.source_key)
            if source is not None:
                source.validation_status = SourceValidationStatus.CHECK_FAILED.value
        await self.session.commit()
        return len(unfinished)

    async def finish_check(
        self,
        check: KnowledgeSourceCheck,
        *,
        result: SourceCheckResult,
        checked_documents: int,
        changed_documents: int,
        failure_code: str | None = None,
    ) -> None:
        """Record an outcome without invalidating an older current document on error."""

        now = utc_now()
        # A failed document causes an explicit rollback in the worker. SQLAlchemy
        # expires ORM attributes on rollback, so update this audit row by its
        # immutable identity instead of lazily reloading an expired instance.
        identity = inspect(check).identity
        if not identity:
            raise RuntimeError("source check has no persisted identity")
        check_id = str(identity[0])
        source_key = await self.session.scalar(
            select(KnowledgeSourceCheck.source_key).where(KnowledgeSourceCheck.id == check_id)
        )
        if source_key is None:
            raise RuntimeError("source check is missing")
        await self.session.execute(
            update(KnowledgeSourceCheck)
            .where(KnowledgeSourceCheck.id == check_id)
            .values(
                completed_at=now,
                result=result.value,
                checked_documents=checked_documents,
                changed_documents=changed_documents,
                failure_code=failure_code,
            )
        )
        source = await self.session.get(KnowledgeSource, source_key)
        if source is not None:
            if result is not SourceCheckResult.FAILED:
                source.last_successful_check_at = now
                source.validation_status = SourceValidationStatus.APPROVED.value
            else:
                source.validation_status = SourceValidationStatus.CHECK_FAILED.value
            if changed_documents:
                source.last_detected_change_at = now
            if result is SourceCheckResult.CHANGED:
                source.last_successful_ingestion_at = now
        await self.session.commit()

    async def latest_version(self, *, source_key: str, canonical_url: str) -> KnowledgeDocumentVersion | None:
        statement = (
            select(KnowledgeDocumentVersion)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
            .where(KnowledgeDocument.source_key == source_key, KnowledgeDocument.canonical_url == canonical_url)
            .order_by(KnowledgeDocumentVersion.version_number.desc())
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def record_document_version(
        self,
        *,
        source_key: str,
        canonical_url: str,
        source_url: str,
        title: str,
        content_hash: str,
        extraction_method: str,
        is_ocr: bool,
        ocr_confidence: float | None,
        source_metadata: dict[str, str],
        last_modified_at: datetime | None = None,
        publication_at: datetime | None = None,
        effective_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[KnowledgeDocumentVersion, bool]:
        """Create one new immutable version only when the content hash changed."""

        latest = await self.latest_version(source_key=source_key, canonical_url=canonical_url)
        now = utc_now()
        if (
            latest is not None
            and latest.content_hash == content_hash
            and latest.status == DocumentStatus.CURRENT.value
        ):
            latest.last_checked_at = now
            latest.source_metadata = source_metadata
            latest.last_modified_at = last_modified_at or latest.last_modified_at
            return latest, False

        document = await self.session.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_key == source_key,
                KnowledgeDocument.canonical_url == canonical_url,
            )
        )
        if document is None:
            document = KnowledgeDocument(
                id=str(uuid4()),
                source_key=source_key,
                canonical_url=canonical_url,
                title=title[:500],
                source_metadata=source_metadata,
            )
            self.session.add(document)
            await self.session.flush()
        else:
            document.title = title[:500]
            document.source_metadata = source_metadata

        # A failed extraction can exist after the last usable version. Promote
        # only one successful replacement by superseding every prior CURRENT
        # version of this logical document, never by deleting audit history.
        await self.session.execute(
            update(KnowledgeDocumentVersion)
            .where(
                KnowledgeDocumentVersion.document_id == document.id,
                KnowledgeDocumentVersion.status == DocumentStatus.CURRENT.value,
            )
            .values(status=DocumentStatus.SUPERSEDED.value)
        )
        version = KnowledgeDocumentVersion(
            id=str(uuid4()),
            document_id=document.id,
            version_number=(latest.version_number + 1) if latest else 1,
            source_url=source_url,
            title=title[:500],
            content_hash=content_hash,
            status=DocumentStatus.CURRENT.value,
            publication_at=publication_at,
            effective_at=effective_at,
            expires_at=expires_at,
            first_retrieved_at=now,
            last_checked_at=now,
            last_modified_at=last_modified_at,
            storage_reference=source_url,
            extraction_method=extraction_method,
            is_ocr=is_ocr,
            ocr_confidence=ocr_confidence,
            source_metadata=source_metadata,
        )
        self.session.add(version)
        await self.session.flush()
        return version, True

    async def add_chunks(
        self,
        *,
        document_version_id: str,
        chunks: list[dict[str, object]],
    ) -> list[KnowledgeChunk]:
        """Persist chunks once; the caller indexes these exact IDs into Qdrant."""

        stored: list[KnowledgeChunk] = []
        for ordinal, chunk in enumerate(chunks):
            stored_chunk = KnowledgeChunk(
                id=str(uuid4()),
                document_version_id=document_version_id,
                ordinal=ordinal,
                heading=_optional_string(chunk.get("heading"), 500),
                content=str(chunk["content"]),
                content_hash=str(chunk["content_hash"]),
                vector_point_id=str(uuid4()),
                page_number=_optional_int(chunk.get("page_number")),
                language=_optional_string(chunk.get("language"), 24),
                state=_optional_string(chunk.get("state"), 100),
                district=_optional_string(chunk.get("district"), 120),
                scheme_key=_optional_string(chunk.get("scheme_key"), 120),
            )
            self.session.add(stored_chunk)
            stored.append(stored_chunk)
        await self.session.flush()
        return stored

    async def vector_point_ids_for_version(self, document_version_id: str) -> list[str]:
        """Return vector IDs before a CURRENT version is superseded."""

        return list(
            (await self.session.scalars(
                select(KnowledgeChunk.vector_point_id).where(KnowledgeChunk.document_version_id == document_version_id)
            )).all()
        )

    async def current_vector_point_ids(self, *, source_key: str, canonical_url: str) -> list[str]:
        """Find vectors whose Qdrant status must change before replacement."""

        statement = (
            select(KnowledgeChunk.vector_point_id)
            .join(KnowledgeDocumentVersion, KnowledgeDocumentVersion.id == KnowledgeChunk.document_version_id)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
            .where(
                KnowledgeDocument.source_key == source_key,
                KnowledgeDocument.canonical_url == canonical_url,
                KnowledgeDocumentVersion.status == DocumentStatus.CURRENT.value,
            )
        )
        return list((await self.session.scalars(statement)).all())

    async def current_chunks_for_vector_points(self, point_ids: list[str]) -> list[tuple[KnowledgeChunk, KnowledgeDocumentVersion, KnowledgeDocument, KnowledgeSource]]:
        """Resolve Qdrant hits through current relational source/version metadata."""

        if not point_ids:
            return []
        ordering = {point_id: index for index, point_id in enumerate(point_ids)}
        statement: Select[tuple[KnowledgeChunk, KnowledgeDocumentVersion, KnowledgeDocument, KnowledgeSource]] = (
            select(KnowledgeChunk, KnowledgeDocumentVersion, KnowledgeDocument, KnowledgeSource)
            .join(KnowledgeDocumentVersion, KnowledgeDocumentVersion.id == KnowledgeChunk.document_version_id)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
            .join(KnowledgeSource, KnowledgeSource.key == KnowledgeDocument.source_key)
            .where(
                KnowledgeChunk.vector_point_id.in_(point_ids),
                KnowledgeDocumentVersion.status == DocumentStatus.CURRENT.value,
                KnowledgeSource.enabled.is_(True),
                KnowledgeSource.validation_status == SourceValidationStatus.APPROVED.value,
            )
        )
        rows = list((await self.session.execute(statement)).all())
        return sorted(rows, key=lambda row: ordering[row[0].vector_point_id])

    async def admin_dashboard_snapshot(self, *, recent_document_limit: int = 30) -> dict[str, object]:
        """Return non-sensitive, operational metadata for the admin dashboard.

        Raw chunk text, embedding values, content hashes, and provider secrets
        deliberately remain unavailable to the browser, including to this
        dashboard. Administrators can inspect official source links and the
        ingestion audit without turning the dashboard into a data exfiltration
        surface.
        """

        sources = list(
            (
                await self.session.scalars(
                    select(KnowledgeSource).order_by(KnowledgeSource.authority_level.desc(), KnowledgeSource.name)
                )
            ).all()
        )
        document_count = int(
            await self.session.scalar(select(func.count()).select_from(KnowledgeDocument)) or 0
        )
        current_document_count = int(
            await self.session.scalar(
                select(func.count())
                .select_from(KnowledgeDocumentVersion)
                .where(KnowledgeDocumentVersion.status == DocumentStatus.CURRENT.value)
            )
            or 0
        )
        chunk_count = int(
            await self.session.scalar(select(func.count()).select_from(KnowledgeChunk)) or 0
        )

        source_rows: list[dict[str, object]] = []
        for source in sources:
            current_documents = int(
                await self.session.scalar(
                    select(func.count())
                    .select_from(KnowledgeDocumentVersion)
                    .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
                    .where(
                        KnowledgeDocument.source_key == source.key,
                        KnowledgeDocumentVersion.status == DocumentStatus.CURRENT.value,
                    )
                )
                or 0
            )
            source_chunks = int(
                await self.session.scalar(
                    select(func.count())
                    .select_from(KnowledgeChunk)
                    .join(
                        KnowledgeDocumentVersion,
                        KnowledgeDocumentVersion.id == KnowledgeChunk.document_version_id,
                    )
                    .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
                    .where(KnowledgeDocument.source_key == source.key)
                )
                or 0
            )
            latest_check = await self.session.scalar(
                select(KnowledgeSourceCheck)
                .where(KnowledgeSourceCheck.source_key == source.key)
                .order_by(KnowledgeSourceCheck.started_at.desc())
                .limit(1)
            )
            source_rows.append(
                {
                    "key": source.key,
                    "name": source.name,
                    "category": source.category,
                    "geographic_scope": source.geographic_scope,
                    "approved_domains": list(source.approved_domains),
                    "entry_urls": list(source.entry_urls),
                    "enabled": source.enabled,
                    "validation_status": source.validation_status,
                    "check_interval_hours": source.check_interval_hours,
                    "last_successful_check_at": source.last_successful_check_at,
                    "last_detected_change_at": source.last_detected_change_at,
                    "last_successful_ingestion_at": source.last_successful_ingestion_at,
                    "current_document_count": current_documents,
                    "chunk_count": source_chunks,
                    "latest_check": (
                        {
                            "started_at": latest_check.started_at,
                            "completed_at": latest_check.completed_at,
                            "result": latest_check.result,
                            "checked_documents": latest_check.checked_documents,
                            "changed_documents": latest_check.changed_documents,
                            "failure_code": latest_check.failure_code,
                        }
                        if latest_check is not None
                        else None
                    ),
                }
            )

        recent_rows = list(
            (
                await self.session.execute(
                    select(KnowledgeDocumentVersion, KnowledgeDocument, KnowledgeSource)
                    .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
                    .join(KnowledgeSource, KnowledgeSource.key == KnowledgeDocument.source_key)
                    .order_by(KnowledgeDocumentVersion.last_checked_at.desc())
                    .limit(recent_document_limit)
                )
            ).all()
        )
        recent_documents = [
            {
                "source_key": source.key,
                "source_name": source.name,
                "title": version.title,
                "url": version.source_url,
                "version_number": version.version_number,
                "status": version.status,
                "last_checked_at": version.last_checked_at,
                "first_retrieved_at": version.first_retrieved_at,
                "extraction_method": version.extraction_method,
                "is_ocr": version.is_ocr,
            }
            for version, _document, source in recent_rows
        ]
        return {
            "source_count": len(sources),
            "document_count": document_count,
            "current_document_count": current_document_count,
            "chunk_count": chunk_count,
            "sources": source_rows,
            "recent_documents": recent_documents,
        }


def _source_values(definition: ApprovedSourceDefinition) -> dict[str, object]:
    return {
        "key": definition.key,
        "name": definition.name,
        "category": definition.category,
        "authority_level": definition.authority_level,
        "geographic_scope": definition.geographic_scope,
        "check_interval_hours": definition.check_interval_hours,
        "approved_domains": list(definition.approved_domains),
        "entry_urls": list(definition.entry_urls),
        "discovery_path_prefixes": list(definition.discovery_path_prefixes),
        "max_documents_per_check": definition.max_documents_per_check,
        "enabled": definition.enabled,
        "validation_status": SourceValidationStatus.APPROVED.value,
    }


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _optional_string(value: object, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized[:max_length] if normalized else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None
