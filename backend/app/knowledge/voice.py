"""Voice-turn grounding without sending citations to speech synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.session import get_session_factory
from app.config.settings import Settings
from app.knowledge.contracts import Citation, EvidenceStatus, RetrievalResult, UserKnowledgeContext
from app.knowledge.policy import decide_response
from app.knowledge.retrieval import KnowledgeRetriever, format_evidence_for_model


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
        if session_factory is not None:
            try:
                async with session_factory() as session:
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

        decision = decide_response(
            message=message,
            language=language,
            retrieval=retrieval,
            has_reference_document=has_reference_document,
        )
        if decision.requires_abstention:
            reply = decision.abstention_message or "That detail is not yet available in Sahayak AI's knowledge base."
            instructions = (
                "VERIFIED KNOWLEDGE POLICY: No current verified evidence supports this "
                f"authoritative request. Reply exactly with this text and do not add facts: {reply}"
            )
        elif decision.retrieval.evidence:
            instructions = (
                "VERIFIED KNOWLEDGE EVIDENCE START\n"
                f"{format_evidence_for_model(decision.retrieval.evidence)}\n"
                "VERIFIED KNOWLEDGE EVIDENCE END\n"
                "Use authoritative facts only from this evidence. If it does not support a "
                "detail, say that it is not yet available in Sahayak AI's knowledge base. "
                "Do not name sources, citations, or URLs aloud."
            )
        else:
            instructions = (
                "No verified source evidence was retrieved for this question. Keep any answer "
                "general and educational; do not present it as a current official, legal, "
                "financial, scheme, eligibility, deadline, claim, contact, or procedural fact. "
                "If a user-provided document is in the context, explain only what that document "
                "says and do not treat it as confirmation of a current rule."
            )

        return VoiceKnowledgeTurn(
            evidence_status=decision.evidence_status,
            citations=decision.retrieval.citations,
            instructions=instructions,
        )
