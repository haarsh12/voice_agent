"""Voice-turn grounding without sending citations to speech synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.session import get_session_factory
from app.config.settings import Settings
from app.knowledge.contracts import Citation, EvidenceStatus, RetrievalResult, UserKnowledgeContext
from app.knowledge.policy import decide_response
from app.knowledge.retrieval import KnowledgeRetriever, format_evidence_for_model
from app.schemes.repository import SchemeRepository
from app.schemes.voice import SchemeVoiceResult, discover_for_voice, is_next_page_request


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

        session_factory = get_session_factory()
        retrieval = RetrievalResult(unavailable_reason="verified_knowledge_database_unavailable")
        scheme_result: SchemeVoiceResult | None = None
        if session_factory is not None:
            try:
                async with session_factory() as session:
                    retriever = KnowledgeRetriever(session, self.settings)
                    retrieval = (
                        await retriever.retrieve(message, user_context=user_context)
                        if user_context is not None
                        else await retriever.retrieve(message)
                    )
                    scheme_repository = SchemeRepository(session)
                    query_for_scheme = (
                        self._last_scheme_query
                        if is_next_page_request(message) and self._last_scheme_query
                        else message
                    )
                    next_offset = self._last_scheme_offset + 3 if query_for_scheme != message else 0
                    scheme_result = await discover_for_voice(
                        scheme_repository,
                        message=query_for_scheme,
                        context=user_context,
                        offset=next_offset,
                    )
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
            except Exception:
                # The chat policy turns an unavailable source layer into a
                # safe abstention for authoritative requests. Do not surface a
                # database/Qdrant error to the caller or the model.
                retrieval = RetrievalResult(unavailable_reason="verified_retrieval_unavailable")
                scheme_result = None

        decision = decide_response(
            message=message,
            language=language,
            retrieval=retrieval,
            has_reference_document=has_reference_document,
        )
        if decision.requires_abstention:
            reply = decision.abstention_message or "I can provide general information about this."
            instructions = (
                "RESPONSE POLICY: No verified evidence for this specific detail. "
                f"Provide this helpful response: {reply} "
                "Then give brief general guidance if you have relevant knowledge. "
                "NEVER mention 'knowledge base' or 'database' or 'verified sources'."
            )
        elif decision.retrieval.evidence:
            instructions = (
                "OFFICIAL EVIDENCE START\n"
                f"{format_evidence_for_model(decision.retrieval.evidence)}\n"
                "OFFICIAL EVIDENCE END\n"
                "Answer using the facts from this evidence. If a specific detail isn't covered, "
                "say you can help with general information about that topic. "
                "NEVER mention 'sources', 'knowledge base', 'database', or 'citations' in speech. "
                "Speak naturally as if you simply know this information."
            )
        else:
            instructions = (
                "GENERAL RESPONSE MODE\n"
                "Provide helpful information using your knowledge. Guidelines:\n"
                "1. Answer naturally without prefacing with 'generally' unless contextually appropriate\n"
                "2. Don't claim specific current amounts, deadlines, or eligibility criteria as facts\n"
                "3. NEVER redirect to websites or portals\n"
                "4. NEVER mention 'knowledge base', 'database', 'verified sources', or 'official information'\n"
                "5. Keep responses conversational and helpful\n"
                "6. If asked about schemes, describe what typically exists\n"
                "The UI handles marking this as general guidance - you just provide helpful answers."
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
