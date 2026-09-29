"""Online hybrid retrieval: Qdrant similarity followed by relational validation."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.knowledge.contracts import Citation, DocumentStatus, RetrievedEvidence, RetrievalResult, UserKnowledgeContext
from app.knowledge.registry import SOURCES_BY_KEY, is_approved_source_url
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.vectors import QdrantVectorStore, VertexEmbeddingProvider

logger = logging.getLogger("sahayak.knowledge.retrieval")


class KnowledgeRetriever:
    """Fast query-time path; it never fetches, extracts, or indexes sources."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.repository = KnowledgeRepository(session)
        self.settings = settings
        self.vector_store = QdrantVectorStore(settings)
        self.embedding_provider = VertexEmbeddingProvider(settings)

    async def retrieve(self, query: str, *, user_context: UserKnowledgeContext | None = None) -> RetrievalResult:
        started_at = time.perf_counter()
        if not self.vector_store.configured:
            logger.info("knowledge_retrieval_skipped reason=not_configured")
            return RetrievalResult(unavailable_reason="verified_knowledge_not_configured")
        try:
            vectors = await asyncio.to_thread(self.embedding_provider.embed, [query])
            filters = {"document_status": DocumentStatus.CURRENT.value}
            if user_context and user_context.state:
                # A national chunk has no state payload; state-specific ranking
                # is finalised by the relational layer below.
                filters = {"document_status": DocumentStatus.CURRENT.value}
            hits = await asyncio.to_thread(
                self.vector_store.search,
                vectors[0],
                # Several top vector hits may be filtered out later because a
                # source check failed or a version changed. Oversample at the
                # vector layer, then retain only relationally CURRENT,
                # approved evidence below.
                limit=min(self.settings.knowledge_retrieval_limit * 5, 100),
                filters=filters,
            )
        except Exception:
            # The precise provider failure may contain infrastructure detail.
            # It is retained neither in the browser response nor model prompt.
            logger.warning("knowledge_retrieval_unavailable")
            return RetrievalResult(unavailable_reason="verified_retrieval_unavailable")

        score_by_id = {hit.point_id: hit.score for hit in hits}
        rows = await self.repository.current_chunks_for_vector_points([hit.point_id for hit in hits])
        evidence: list[RetrievedEvidence] = []
        now = datetime.now(UTC)
        for chunk, version, document, source in rows:
            if version.expires_at and _as_utc(version.expires_at) < now:
                continue
            definition = SOURCES_BY_KEY.get(source.key)
            if definition is None or not is_approved_source_url(version.source_url, definition):
                continue
            if not _applies_to_user(chunk.state, chunk.district, user_context):
                continue
            citation = Citation(
                source_name=source.name,
                title=version.title,
                url=version.source_url,
                document_version=str(version.version_number),
                published_at=version.publication_at,
                effective_at=version.effective_at,
                freshness_status=DocumentStatus(version.status),
            )
            evidence.append(
                RetrievedEvidence(
                    chunk_id=chunk.id,
                    text=chunk.content,
                    score=score_by_id[chunk.vector_point_id],
                    citation=citation,
                    source_priority=source.authority_level,
                    state=chunk.state,
                    district=chunk.district,
                    language=chunk.language,
                )
            )
        evidence.sort(key=lambda item: (_geographic_score(item, user_context), item.source_priority, item.score), reverse=True)
        logger.info(
            "knowledge_retrieval_complete evidence=%s latency_ms=%s",
            len(evidence),
            round((time.perf_counter() - started_at) * 1_000),
        )
        return RetrievalResult(evidence=tuple(evidence[: self.settings.knowledge_retrieval_limit]))


def format_evidence_for_model(evidence: tuple[RetrievedEvidence, ...], *, max_characters: int = 10_000) -> str:
    """Pass compact, source-labelled facts to Gemini without giving it URLs to invent."""

    blocks: list[str] = []
    used = 0
    for item in evidence:
        block = f"SOURCE: {item.citation.source_name}\nTITLE: {item.citation.title}\nCONTENT:\n{item.text}".strip()
        if used + len(block) > max_characters:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n---\n\n".join(blocks)


def _applies_to_user(state: str | None, district: str | None, context: UserKnowledgeContext | None) -> bool:
    if context is None:
        return state is None and district is None
    if state and state.casefold() != (context.state or "").casefold():
        return False
    if district and district.casefold() != (context.district or "").casefold():
        return False
    return True


def _geographic_score(item: RetrievedEvidence, context: UserKnowledgeContext | None) -> int:
    if context is None:
        return 0
    if item.district and item.district.casefold() == (context.district or "").casefold():
        return 2
    if item.state and item.state.casefold() == (context.state or "").casefold():
        return 1
    return 0


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
