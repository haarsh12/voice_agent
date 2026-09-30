"""Database operations for the canonical, source-derived scheme catalogue."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeSource,
    SchemeRecord,
    SchemeSource,
    SchemeVersion,
)
from app.schemes.contracts import (
    SchemeDetail,
    SchemeSearchPage,
    SchemeSourceReference,
    SchemeStatus,
    SchemeSummary,
    SchemeVerificationStatus,
)
from app.schemes.extraction import ExtractedScheme, extract_schemes_from_document


def utc_now() -> datetime:
    return datetime.now(UTC)


class SchemeRepository:
    """Owns structured scheme records; browsers never write to this store."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_from_document(
        self,
        *,
        source: KnowledgeSource,
        version: KnowledgeDocumentVersion,
        chunks: list[KnowledgeChunk],
    ) -> int:
        """Create/update only deterministic candidates backed by current chunks.

        A content hash prevents version churn for repeated source checks.  When
        source content changes, the prior current snapshot stays auditable but
        becomes ``SUPERSEDED`` before the new snapshot is selected online.
        """

        candidates = extract_schemes_from_document(source=source, version=version, chunks=chunks)
        chunk_by_id = {chunk.id: chunk for chunk in chunks}
        changed_count = 0
        for candidate in candidates:
            scheme = await self.session.scalar(
                select(SchemeRecord).where(SchemeRecord.normalized_name == candidate.normalized_name)
            )
            now = utc_now()
            if scheme is None:
                scheme = SchemeRecord(
                    id=str(uuid4()),
                    slug=candidate.slug,
                    normalized_name=candidate.normalized_name,
                    official_name=candidate.official_name,
                    short_name=_short_name(candidate.official_name),
                    aliases=_aliases(candidate.official_name),
                    scheme_type=candidate.scheme_type,
                    category=candidate.category,
                    ministry=source.name,
                    implementing_authority=source.name,
                    geographic_scope=candidate.geographic_scope,
                    applicable_states=list(candidate.applicable_states),
                    applicable_districts=list(candidate.applicable_districts),
                    beneficiary_categories=list(candidate.beneficiary_categories),
                    relevant_user_types=list(candidate.relevant_user_types),
                    status=SchemeStatus.UNKNOWN.value,
                    verification_status=SchemeVerificationStatus.APPROVED.value,
                    first_discovered_at=now,
                    last_checked_at=now,
                    last_changed_at=now,
                )
                self.session.add(scheme)
                await self.session.flush()
            else:
                scheme.last_checked_at = now
                # A source may contribute extra evidence for a duplicate. Keep
                # the canonical identity stable while unioning source-supported
                # metadata; never replace it from an unverified query.
                scheme.aliases = _merge_strings(scheme.aliases, _aliases(candidate.official_name))
                scheme.applicable_states = _merge_strings(scheme.applicable_states, list(candidate.applicable_states))
                scheme.applicable_districts = _merge_strings(scheme.applicable_districts, list(candidate.applicable_districts))
                scheme.beneficiary_categories = _merge_strings(
                    scheme.beneficiary_categories, list(candidate.beneficiary_categories)
                )
                scheme.relevant_user_types = _merge_strings(
                    scheme.relevant_user_types, list(candidate.relevant_user_types)
                )

            content_hash = _candidate_hash(candidate)
            current = await self.session.scalar(
                select(SchemeVersion)
                .where(SchemeVersion.scheme_id == scheme.id, SchemeVersion.is_current.is_(True))
                .order_by(SchemeVersion.version_number.desc())
                .limit(1)
            )
            current_has_document = False
            if current is not None:
                current_has_document = bool(
                    await self.session.scalar(
                        select(SchemeSource.id).where(
                            SchemeSource.scheme_version_id == current.id,
                            SchemeSource.document_version_id == version.id,
                        )
                    )
                )
            if current is not None and current.content_hash == content_hash:
                current.last_checked_at = now
                await self._link_evidence(
                    scheme_version=current,
                    source=source,
                    document_version=version,
                    chunk_by_id=chunk_by_id,
                    candidate=candidate,
                )
                continue

            if current is not None and not current_has_document:
                # A second official document is corroborating evidence for the
                # same current programme, not a replacement of the first
                # source's facts.  Preserve both links on one canonical
                # snapshot; a later changed version of either document does
                # create a new audited snapshot.
                await self._link_evidence(
                    scheme_version=current,
                    source=source,
                    document_version=version,
                    chunk_by_id=chunk_by_id,
                    candidate=candidate,
                )
                continue

            if current is not None:
                current.is_current = False
                current.status = SchemeStatus.SUPERSEDED.value
            next_number = (current.version_number if current is not None else 0) + 1
            stored = SchemeVersion(
                id=str(uuid4()),
                scheme_id=scheme.id,
                version_number=next_number,
                content_hash=content_hash,
                # A current source document does not prove that applications
                # are open or that a benefit is active. Keep that distinction.
                status=SchemeStatus.UNKNOWN.value,
                verification_status=SchemeVerificationStatus.APPROVED.value,
                data=candidate.data,
                evidence_summary=candidate.evidence_summary,
                publication_at=version.publication_at,
                effective_at=version.effective_at,
                expires_at=version.expires_at,
                first_retrieved_at=now,
                last_checked_at=now,
                last_changed_at=now,
                is_current=True,
            )
            self.session.add(stored)
            await self.session.flush()
            scheme.current_version_number = next_number
            scheme.last_changed_at = now
            await self._link_evidence(
                scheme_version=stored,
                source=source,
                document_version=version,
                chunk_by_id=chunk_by_id,
                candidate=candidate,
            )
            for chunk_id in candidate.chunk_ids:
                chunk = chunk_by_id.get(chunk_id)
                if chunk is not None and chunk.scheme_key is None:
                    # A semantic chunk may support more than one entity.  Its
                    # source links retain that many-to-many history; this field
                    # is only a safe primary retrieval hint.
                    chunk.scheme_key = scheme.id
            changed_count += 1
        return changed_count

    async def sync_current_documents(self) -> int:
        """Backfill catalogue records from already-ingested official content.

        This is an offline maintenance action, not a request-time crawl.  It
        lets an installed knowledge base become useful immediately without
        inventing a seed list or re-downloading a source.
        """

        rows = list(
            (
                await self.session.execute(
                    select(KnowledgeDocumentVersion, KnowledgeSource)
                    .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentVersion.document_id)
                    .join(KnowledgeSource, KnowledgeSource.key == KnowledgeDocument.source_key)
                    .where(KnowledgeDocumentVersion.status == "CURRENT")
                )
            ).all()
        )
        count = 0
        for version, source in rows:
            chunks = list(
                (
                    await self.session.scalars(
                        select(KnowledgeChunk)
                        .where(KnowledgeChunk.document_version_id == version.id)
                        .order_by(KnowledgeChunk.ordinal)
                    )
                ).all()
            )
            count += await self.upsert_from_document(source=source, version=version, chunks=chunks)
        # Records created by an earlier permissive parser remain auditable but
        # must not remain public once deterministic quality checks reject their
        # headline-style label or a duplicate dedicated-source label.
        await self.session.execute(
            update(SchemeRecord)
            .where(
                or_(
                    SchemeRecord.official_name.ilike("Union Minister %"),
                    SchemeRecord.official_name.ilike("Minister %"),
                    SchemeRecord.official_name.ilike("MoS %"),
                    SchemeRecord.official_name.ilike("Launch of %"),
                    (
                        SchemeRecord.official_name.ilike("%PMFBY%")
                        & (SchemeRecord.normalized_name != "pradhan mantri fasal bima yojana (pmfby)")
                    ),
                    SchemeRecord.official_name.ilike("Cabinet %"),
                    SchemeRecord.official_name.ilike("%?%"),
                    SchemeRecord.official_name.ilike("%HEARING NOTICE%"),
                    (
                        SchemeRecord.id.in_(
                            select(SchemeVersion.scheme_id)
                            .join(SchemeSource, SchemeSource.scheme_version_id == SchemeVersion.id)
                            .where(SchemeSource.source_key == "cpgrams")
                        )
                        & (SchemeRecord.normalized_name != "centralized public grievance redress and monitoring system (cpgrams)")
                    ),
                )
            )
            .values(verification_status=SchemeVerificationStatus.REVIEW_REQUIRED.value)
        )
        await self.session.commit()
        return count

    async def list_schemes(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        beneficiary: str | None = None,
        state: str | None = None,
        district: str | None = None,
        include_unknown_status: bool = True,
        limit: int = 24,
        offset: int = 0,
    ) -> SchemeSearchPage:
        """Query current, verified records then apply portable JSON filters.

        JSON membership differs across SQLite and PostgreSQL.  We retain a
        modest, bounded candidate set and filter in Python so both deployed
        databases have identical correctness behaviour.
        """

        statement: Select[tuple[SchemeRecord, SchemeVersion]] = (
            select(SchemeRecord, SchemeVersion)
            .join(SchemeVersion, SchemeVersion.scheme_id == SchemeRecord.id)
            .where(
                SchemeVersion.is_current.is_(True),
                SchemeRecord.verification_status == SchemeVerificationStatus.APPROVED.value,
                SchemeVersion.verification_status == SchemeVerificationStatus.APPROVED.value,
            )
            .order_by(SchemeRecord.last_changed_at.desc(), SchemeRecord.official_name)
            .limit(500)
        )
        if not include_unknown_status:
            statement = statement.where(SchemeRecord.status.in_((SchemeStatus.ACTIVE.value, SchemeStatus.APPLICATION_OPEN.value)))
        terms = _query_terms(query)
        rows = list((await self.session.execute(statement)).all())
        matched = [
            (record, version)
            for record, version in rows
            if _matches_filters(record, category=category, beneficiary=beneficiary, state=state, district=district)
            and _matches_query(record, version, terms)
        ]
        matched.sort(key=lambda row: _rank(row[0], query=query, beneficiary=beneficiary, state=state, district=district), reverse=True)
        page = matched[offset : offset + limit]
        return SchemeSearchPage(
            items=tuple(_summary(record, version) for record, version in page),
            total=len(matched),
            offset=offset,
            limit=limit,
        )

    async def get_scheme(self, identifier: str) -> SchemeDetail | None:
        """Return one current verified record by public UUID or safe slug."""

        record = await self.session.scalar(
            select(SchemeRecord).where(
                SchemeRecord.verification_status == SchemeVerificationStatus.APPROVED.value,
                or_(SchemeRecord.id == identifier, SchemeRecord.slug == identifier),
            )
        )
        if record is None:
            return None
        version = await self.session.scalar(
            select(SchemeVersion).where(
                SchemeVersion.scheme_id == record.id,
                SchemeVersion.is_current.is_(True),
                SchemeVersion.verification_status == SchemeVerificationStatus.APPROVED.value,
            )
        )
        if version is None:
            return None
        source_rows = list(
            (
                await self.session.execute(
                    select(SchemeSource, KnowledgeDocumentVersion.version_number)
                    .join(KnowledgeDocumentVersion, KnowledgeDocumentVersion.id == SchemeSource.document_version_id)
                    .where(SchemeSource.scheme_version_id == version.id)
                    .order_by(SchemeSource.source_name, SchemeSource.document_title)
                )
            ).all()
        )
        return SchemeDetail(
            **_summary(record, version).__dict__,
            data=dict(version.data),
            sources=tuple(
                SchemeSourceReference(
                    source_name=row.source_name,
                    title=row.document_title,
                    url=row.source_url,
                    relevant_section=row.relevant_section,
                    page_number=row.page_number,
                    document_version=document_version,
                )
                for row, document_version in source_rows
            ),
            current_version_number=version.version_number,
        )

    async def filter_options(self) -> dict[str, list[str]]:
        """Return only filter values represented by verified current records."""

        rows = list(
            (
                await self.session.scalars(
                    select(SchemeRecord)
                    .join(SchemeVersion, SchemeVersion.scheme_id == SchemeRecord.id)
                    .where(
                        SchemeVersion.is_current.is_(True),
                        SchemeRecord.verification_status == SchemeVerificationStatus.APPROVED.value,
                        SchemeVersion.verification_status == SchemeVerificationStatus.APPROVED.value,
                    )
                    .limit(500)
                )
            ).all()
        )
        return {
            "categories": sorted({row.category for row in rows}),
            "beneficiaries": sorted({value for row in rows for value in row.relevant_user_types}),
            "states": sorted({value for row in rows for value in row.applicable_states}),
            "types": sorted({row.scheme_type for row in rows}),
        }

    async def evidence_for_schemes(self, scheme_ids: list[str], *, limit: int = 6):
        """Return trusted chunks linked to current catalogue records.

        The normal policy engine can therefore treat a scheme directory result
        exactly like all other verified evidence instead of granting a voice-
        only exception.
        """

        from app.knowledge.contracts import Citation, DocumentStatus, RetrievedEvidence

        if not scheme_ids:
            return ()
        rows = list(
            (
                await self.session.execute(
                    select(SchemeSource, KnowledgeChunk, KnowledgeDocumentVersion, KnowledgeSource)
                    .join(KnowledgeChunk, KnowledgeChunk.id == SchemeSource.chunk_id)
                    .join(KnowledgeDocumentVersion, KnowledgeDocumentVersion.id == SchemeSource.document_version_id)
                    .join(KnowledgeSource, KnowledgeSource.key == SchemeSource.source_key)
                    .join(SchemeVersion, SchemeVersion.id == SchemeSource.scheme_version_id)
                    .where(
                        SchemeVersion.is_current.is_(True),
                        SchemeVersion.verification_status == SchemeVerificationStatus.APPROVED.value,
                        KnowledgeDocumentVersion.status == "CURRENT",
                        KnowledgeSource.enabled.is_(True),
                        KnowledgeSource.validation_status == "APPROVED",
                        SchemeVersion.scheme_id.in_(scheme_ids),
                    )
                    .limit(limit)
                )
            ).all()
        )
        return tuple(
            RetrievedEvidence(
                chunk_id=chunk.id,
                text=chunk.content,
                score=1.0 - index * 0.01,
                citation=Citation(
                    source_name=source.name,
                    title=version.title,
                    url=version.source_url,
                    document_version=str(version.version_number),
                    published_at=version.publication_at,
                    effective_at=version.effective_at,
                    freshness_status=DocumentStatus(version.status),
                ),
                source_priority=source.authority_level,
                state=chunk.state,
                district=chunk.district,
                language=chunk.language,
            )
            for index, (_scheme_source, chunk, version, source) in enumerate(rows)
        )

    async def _link_evidence(
        self,
        *,
        scheme_version: SchemeVersion,
        source: KnowledgeSource,
        document_version: KnowledgeDocumentVersion,
        chunk_by_id: dict[str, KnowledgeChunk],
        candidate: ExtractedScheme,
    ) -> None:
        for chunk_id in candidate.chunk_ids:
            chunk = chunk_by_id.get(chunk_id)
            if chunk is None:
                continue
            exists = await self.session.scalar(
                select(SchemeSource.id).where(
                    SchemeSource.scheme_version_id == scheme_version.id,
                    SchemeSource.document_version_id == document_version.id,
                    SchemeSource.chunk_id == chunk.id,
                )
            )
            if exists is not None:
                continue
            self.session.add(
                SchemeSource(
                    id=str(uuid4()),
                    scheme_version_id=scheme_version.id,
                    source_key=source.key,
                    document_version_id=document_version.id,
                    chunk_id=chunk.id,
                    source_name=source.name,
                    document_title=document_version.title,
                    source_url=document_version.source_url,
                    relevant_section=chunk.heading,
                    page_number=chunk.page_number,
                )
            )


def _candidate_hash(candidate: ExtractedScheme) -> str:
    payload = {
        "name": candidate.normalized_name,
        "type": candidate.scheme_type,
        "category": candidate.category,
        "states": candidate.applicable_states,
        "beneficiaries": candidate.beneficiary_categories,
        "data": candidate.data,
        "evidence": candidate.evidence_summary,
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _short_name(name: str) -> str | None:
    match = __import__("re").search(r"\(([^()]{2,32})\)", name)
    return match.group(1) if match else None


def _aliases(name: str) -> list[str]:
    short = _short_name(name)
    return [name, short] if short else [name]


def _merge_strings(existing: list[str] | None, additions: list[str]) -> list[str]:
    return list(dict.fromkeys([*(existing or []), *additions]))


def _query_terms(value: str | None) -> list[str]:
    if not value:
        return []
    ignored = {"scheme", "schemes", "yojana", "program", "programme", "for", "the", "and", "me", "my", "please", "show", "find", "tell", "about", "what", "which", "available", "hai", "mujhe", "mere", "लिए", "योजना", "कौन", "सी", "माझ्यासाठी", "योजना"}
    return [
        term.strip()[:80]
        for term in value.replace("/", " ").split()
        if len(term.strip()) >= 2 and term.strip().casefold() not in ignored
    ][:8]


def _matches_query(record: SchemeRecord, version: SchemeVersion, terms: list[str]) -> bool:
    if not terms:
        return True
    description = version.data.get("description") if isinstance(version.data, dict) else ""
    searchable = " ".join(
        [
            record.official_name,
            record.short_name or "",
            record.category,
            record.scheme_type,
            *record.aliases,
            *record.beneficiary_categories,
            *record.relevant_user_types,
            *record.applicable_states,
            description if isinstance(description, str) else "",
        ]
    ).casefold()
    return any(term.casefold() in searchable for term in terms)


def _matches_filters(
    record: SchemeRecord, *, category: str | None, beneficiary: str | None, state: str | None, district: str | None
) -> bool:
    if category and record.category.casefold() != category.casefold():
        return False
    if beneficiary and beneficiary not in set(record.relevant_user_types):
        return False
    if state and record.applicable_states and not _contains(record.applicable_states, state):
        return False
    if district and record.applicable_districts and not _contains(record.applicable_districts, district):
        return False
    return True


def _rank(record: SchemeRecord, *, query: str | None, beneficiary: str | None, state: str | None, district: str | None) -> tuple[int, int, int, int, str]:
    query_score = sum(term.casefold() in " ".join([record.official_name, record.category, record.scheme_type, *record.aliases]).casefold() for term in _query_terms(query))
    beneficiary_score = 2 if beneficiary and beneficiary in record.relevant_user_types else 0
    state_score = 2 if state and _contains(record.applicable_states, state) else 1 if not record.applicable_states else 0
    district_score = 2 if district and _contains(record.applicable_districts, district) else 0
    return (state_score, district_score, beneficiary_score, query_score, record.official_name.casefold())


def _contains(values: list[str], expected: str) -> bool:
    return any(value.casefold() == expected.casefold() for value in values)


def _summary(record: SchemeRecord, version: SchemeVersion) -> SchemeSummary:
    description = version.data.get("description") if isinstance(version.data, dict) else None
    return SchemeSummary(
        id=record.id,
        slug=record.slug,
        official_name=record.official_name,
        short_name=record.short_name,
        scheme_type=record.scheme_type,
        category=record.category,
        description=description if isinstance(description, str) else None,
        beneficiary_categories=tuple(record.beneficiary_categories),
        relevant_user_types=tuple(record.relevant_user_types),
        applicable_states=tuple(record.applicable_states),
        applicable_districts=tuple(record.applicable_districts),
        geographic_scope=record.geographic_scope,
        status=SchemeStatus(record.status),
        verification_status=SchemeVerificationStatus(record.verification_status),
        last_checked_at=record.last_checked_at,
    )

