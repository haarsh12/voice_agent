"""Online hybrid retrieval: Qdrant similarity followed by relational validation."""

from __future__ import annotations

import asyncio
import logging
import re
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
        unavailable_reason: str | None = None
        rows: list[tuple[object, object, object, object]] = []
        score_by_id: dict[str, float] = {}
        if not self.vector_store.configured:
            unavailable_reason = "verified_vector_search_not_configured"
            logger.info("knowledge_vector_search_skipped reason=not_configured")
        else:
            try:
                vectors = await asyncio.to_thread(self.embedding_provider.embed, [query])
                hits = await asyncio.to_thread(
                    self.vector_store.search,
                    vectors[0],
                    # Several top vector hits may be filtered out later because a
                    # source check failed or a version changed. Oversample at the
                    # vector layer, then retain only relationally CURRENT,
                    # approved evidence below.
                    limit=min(self.settings.knowledge_retrieval_limit * 5, 100),
                    filters={"document_status": DocumentStatus.CURRENT.value},
                )
                score_by_id = {hit.point_id: hit.score for hit in hits}
                rows = await self.repository.current_chunks_for_vector_points([hit.point_id for hit in hits])
            except Exception:
                # The precise provider failure may contain infrastructure detail.
                # It is retained neither in the browser response nor model prompt.
                unavailable_reason = "verified_vector_search_unavailable"
                logger.warning("knowledge_vector_search_unavailable")

        evidence = _validated_evidence(rows, score_by_id, user_context)
        if not evidence:
            # A current PDF can be in the relational knowledge store while its
            # vector is temporarily absent, stale, or a provider is down. Use
            # a bounded lexical search over the same approved records so the
            # member still receives the information stored in Sahayak AI.
            terms = _search_terms(query)
            if terms:
                try:
                    fallback_rows = await self.repository.current_chunks_for_text_search(
                        terms,
                        limit=min(self.settings.knowledge_retrieval_limit * 25, 200),
                    )
                    lexical_scores = {
                        chunk.vector_point_id: _lexical_score(query, chunk.content, document.title, chunk.heading)
                        for chunk, _version, document, _source in fallback_rows
                    }
                    evidence = _validated_evidence(fallback_rows, lexical_scores, user_context)
                except Exception:
                    # Keep the retrieval failure unobservable to the browser
                    # and fall through to the normal knowledge-base message.
                    logger.warning("knowledge_lexical_search_unavailable")
                    if unavailable_reason is None:
                        unavailable_reason = "verified_lexical_search_unavailable"

        evidence.sort(key=lambda item: (_geographic_score(item, user_context), item.source_priority, item.score), reverse=True)
        logger.info(
            "knowledge_retrieval_complete evidence=%s latency_ms=%s",
            len(evidence),
            round((time.perf_counter() - started_at) * 1_000),
        )
        return RetrievalResult(
            evidence=tuple(evidence[: self.settings.knowledge_retrieval_limit]),
            unavailable_reason=unavailable_reason,
        )


def _validated_evidence(
    rows: list[tuple[object, object, object, object]],
    score_by_id: dict[str, float],
    user_context: UserKnowledgeContext | None,
) -> list[RetrievedEvidence]:
    """Turn already-authorised database rows into display-safe evidence."""

    evidence: list[RetrievedEvidence] = []
    now = datetime.now(UTC)
    for chunk, version, _document, source in rows:
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
                score=score_by_id.get(chunk.vector_point_id, 0.0),
                citation=citation,
                source_priority=source.authority_level,
                state=chunk.state,
                district=chunk.district,
                language=chunk.language,
            )
        )
    return evidence


def _search_terms(query: str) -> list[str]:
    """Extract bounded Unicode terms for parameterised relational matching."""

    terms: list[str] = []
    for term in re.findall(r"[^\W_]{2,}", query.casefold(), flags=re.UNICODE):
        if term not in terms:
            terms.append(term)
        if len(terms) == 12:
            break
    return terms


def _lexical_score(query: str, content: str, title: str, heading: str | None) -> float:
    """Prefer chunks matching more of the member's words without model calls."""

    terms = _search_terms(query)
    haystack = f"{title}\n{heading or ''}\n{content}".casefold()
    matched = sum(term in haystack for term in terms)
    title_or_heading = f"{title}\n{heading or ''}".casefold()
    heading_matches = sum(term in title_or_heading for term in terms)
    return float(matched + heading_matches * 0.25) / max(1, len(terms))


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
