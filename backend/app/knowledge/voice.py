"""Voice-turn grounding without sending citations to speech synthesis."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from app.auth.session import get_session_factory
from app.config.settings import Settings
from app.knowledge.contracts import Citation, EvidenceStatus, RetrievalResult, UserKnowledgeContext
from app.knowledge.policy import decide_response
from app.knowledge.retrieval import KnowledgeRetriever, format_evidence_for_model
from app.schemes.repository import SchemeRepository
from app.schemes.voice import SchemeVoiceResult, discover_for_voice, is_next_page_request


# Keywords that suggest scheme-related queries
_SCHEME_KEYWORDS = frozenset({
    "scheme", "yojana", "योजना", "program", "programme", "benefit", "लाभ",
    "subsidy", "सब्सिडी", "grant", "अनुदान", "assistance", "सहायता",
    "insurance", "बीमा", "pension", "पेंशन", "loan", "ऋण",
})


def _is_scheme_query(message: str) -> bool:
    """Quick check if query likely needs scheme directory search."""
    message_lower = message.lower()
    # Check for scheme keywords
    if any(keyword in message_lower for keyword in _SCHEME_KEYWORDS):
        return True
    # Check for "next" pattern which continues scheme listing
    if is_next_page_request(message):
        return True
    return False


@dataclass(frozen=True)
class VoiceKnowledgeTurn:
    """Grounding for one spoken answer plus visual-only citation metadata."""

    evidence_status: EvidenceStatus
    citations: tuple[Citation, ...]
    instructions: str


class VoiceKnowledgeService:
    """Retrieves before the voice LLM runs; it never fetches or ingests online."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # This instance belongs to one LiveKit participant.  Keeping only a
        # bounded query/offset enables natural “next” turns without persisting
        # voice content or creating a second knowledge store.
        self._last_scheme_query: str | None = None
        self._last_scheme_offset = 0

    async def prepare_turn(
        self,
        *,
        message: str,
        language: str,
        user_context: UserKnowledgeContext | None = None,
        has_reference_document: bool = False,
    ) -> VoiceKnowledgeTurn:
        """Build transient LLM instructions and UI references for one voice turn."""
        
        import time
        start_time = time.time()

        session_factory = get_session_factory()
        retrieval = RetrievalResult(unavailable_reason="verified_knowledge_database_unavailable")
        scheme_result: SchemeVoiceResult | None = None
        
        if session_factory is not None:
            try:
                async with session_factory() as session:
                    # Optimize: Only search schemes if query is scheme-related
                    should_search_schemes = _is_scheme_query(message)
                    
                    if should_search_schemes:
                        # Parallel execution: Run retrieval and scheme search together
                        retriever = KnowledgeRetriever(session, self.settings)
                        scheme_repository = SchemeRepository(session)
                        
                        query_for_scheme = (
                            self._last_scheme_query
                            if is_next_page_request(message) and self._last_scheme_query
                            else message
                        )
                        next_offset = self._last_scheme_offset + 3 if query_for_scheme != message else 0
                        
                        # Run both queries in parallel for speed
                        retrieval_task = asyncio.create_task(
                            retriever.retrieve(message, user_context=user_context)
                            if user_context is not None
                            else retriever.retrieve(message)
                        )
                        scheme_task = asyncio.create_task(
                            discover_for_voice(
                                scheme_repository,
                                message=query_for_scheme,
                                context=user_context,
                                offset=next_offset,
                            )
                        )
                        
                        retrieval, scheme_result = await asyncio.gather(retrieval_task, scheme_task)
                        
                        if scheme_result is not None and scheme_result.page.items:
                            if query_for_scheme == message:
                                self._last_scheme_query = message
                            self._last_scheme_offset = scheme_result.offset
                            catalogue_evidence = await scheme_repository.evidence_for_schemes(
                                [item.id for item in scheme_result.page.items]
                            )
                            # Preserve normal hybrid retrieval while making the
                            # selected catalogue cards first-class, policy-checked
                            # evidence for voice answers.
                            unique = {item.chunk_id: item for item in (*catalogue_evidence, *retrieval.evidence)}
                            retrieval = RetrievalResult(
                                evidence=tuple(unique.values()),
                                unavailable_reason=retrieval.unavailable_reason,
                            )
                    else:
                        # Non-scheme query: just do knowledge retrieval
                        retriever = KnowledgeRetriever(session, self.settings)
                        retrieval = (
                            await retriever.retrieve(message, user_context=user_context)
                            if user_context is not None
                            else await retriever.retrieve(message)
                        )
                        
            except Exception:
                # The chat policy turns an unavailable source layer into a
                # safe abstention for authoritative requests. Do not surface a
                # database/Qdrant error to the caller or the model.
                retrieval = RetrievalResult(unavailable_reason="verified_retrieval_unavailable")
                scheme_result = None
        
        elapsed_ms = (time.time() - start_time) * 1000
        import logging
        logger = logging.getLogger("sahayak.knowledge.voice")
        logger.info(
            "voice_turn_prepared is_scheme=%s has_schemes=%s evidence=%d latency_ms=%.1f",
            should_search_schemes if session_factory else False,
            scheme_result is not None and bool(scheme_result.page.items) if session_factory else False,
            len(retrieval.evidence),
            elapsed_ms,
        )

        decision = decide_response(
            message=message,
            language=language,
            retrieval=retrieval,
            has_reference_document=has_reference_document,
        )
        if decision.requires_abstention:
            # Even without verified evidence, answer the question using general knowledge
            instructions = (
                "Answer this question directly using your general knowledge about government schemes and programs. "
                "Provide helpful, accurate information without saying 'I don't have information' or mentioning databases. "
                "Just answer naturally and confidently. Be brief (2-3 sentences) unless asked for details."
            )
        elif decision.retrieval.evidence:
            instructions = (
                "VERIFIED EVIDENCE:\n"
                f"{format_evidence_for_model(decision.retrieval.evidence)}\n\n"
                "Answer using facts from this evidence. Be direct and confident. "
                "If a detail isn't covered, provide general information about the topic. "
                "NEVER say 'I don't have', 'not available', 'knowledge base', or 'database'. "
                "Just answer naturally."
            )
        else:
            instructions = (
                "Answer this question using your knowledge. "
                "Be helpful and provide accurate general information. "
                "NEVER say 'I don't have information', 'not available', 'knowledge base', or 'database'. "
                "Don't claim specific current amounts, deadlines, or eligibility as definite facts. "
                "NEVER redirect to websites. "
                "Just answer naturally and helpfully in 2-3 sentences."
            )

        if scheme_result is not None and scheme_result.page.items and not decision.requires_abstention:
            names = "\n".join(
                f"- {item.official_name} ({item.scheme_type}; {item.category})"
                for item in scheme_result.page.items
            )
            more = max(scheme_result.page.total - (scheme_result.offset + len(scheme_result.page.items)), 0)
            instructions += (
                "\nSCHEME DIRECTORY RESULTS START\n"
                f"Intent: {scheme_result.intent.value}. Results shown: {len(scheme_result.page.items)}. "
                f"More verified records: {more}.\n{names}\n"
                "SCHEME DIRECTORY RESULTS END\n"
                "Speak a short helpful answer using only these named records and the verified evidence. "
                "Do not say a person is definitely eligible. Explain that eligibility, benefits, documents, "
                "deadlines, and application steps must be stated in the evidence; say a specific detail is "
                "not available in Sahayak AI's knowledge base when absent. Do not mention URLs or send the "
                "user to another website. If more records remain, offer to continue with the next three or "
                "ask whether they prefer insurance, financial support, cooperative support, or a specific scheme."
            )
        elif scheme_result is not None and not scheme_result.page.items:
            instructions += (
                "\nSCHEME DIRECTORY POLICY: No verified matching catalogue record was found. "
                "Do not invent a scheme or a current condition. Ask one short, useful follow-up about "
                "the user's category, state, or type of support, and keep guidance inside Sahayak AI."
            )

        return VoiceKnowledgeTurn(
            evidence_status=decision.evidence_status,
            citations=decision.retrieval.citations,
            instructions=instructions,
        )
