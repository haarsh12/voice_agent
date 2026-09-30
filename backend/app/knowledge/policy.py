"""Evidence policy that prevents unsupported official-looking answers."""

from __future__ import annotations

from app.knowledge.contracts import EvidenceStatus, KnowledgeDecision, RetrievedEvidence, RetrievalResult

_AUTHORITATIVE_TERMS = (
    "scheme", "eligibility", "eligible", "benefit", "deadline", "last date", "apply", "application",
    "claim", "premium", "insurance", "pmfby", "notification", "circular", "law", "legal", "rule",
    "bylaw", "bye-law", "procedure", "process", "contact", "helpline", "grievance", "loan", "interest",
    "current", "latest", "new", "official", "website", "portal", "bank", "pnb",
    "योजना", "पात्रता", "लाभ", "अंतिम तिथि", "आवेदन", "दावा", "बीमा", "नियम", "कानून", "शिकायत",
    "अधिसूचना", "प्रक्रिया", "कर्ज", "ब्याज", "वर्तमान", "नवीनतम", "नई", "नया", "आधिकारिक",
    "वेबसाइट", "पोर्टल", "बैंक", "पीएनबी", "योजने", "पात्र", "अर्ज", "विमा", "नियम",
)

_ABSTENTIONS = {
    "hi-IN": "यह वर्तमान जानकारी अभी सहायाक एआई के ज्ञान आधार में उपलब्ध नहीं है। मैं आपकी स्थिति और जरूरी दस्तावेज़ समझकर आगे की तैयारी में मदद कर सकती हूँ।",
    "mr-IN": "ही सध्याची माहिती सहायाक एआयच्या ज्ञानसंग्रहात अजून उपलब्ध नाही. तुमची परिस्थिती आणि आवश्यक कागदपत्रे समजून पुढील तयारीत मी मदत करू शकते.",
    "en-IN": "That current detail is not yet available in Sahayak AI's knowledge base. I can still help you understand your situation and prepare the information or documents needed next.",
    "ta-IN": "இந்த தற்போதைய விவரம் சஹாயக் ஏஐ அறிவுத் தளத்தில் இன்னும் இல்லை. உங்கள் நிலை மற்றும் அடுத்ததாகத் தேவையான ஆவணங்களைப் புரிந்துகொள்ள நான் உதவ முடியும்.",
    "te-IN": "ఈ తాజా వివరాలు సహాయక్ ఏఐ జ్ఞాన భాండాగారంలో ఇంకా అందుబాటులో లేవు. మీ పరిస్థితి మరియు తర్వాత అవసరమైన పత్రాలను అర్థం చేసుకోవడంలో నేను సహాయం చేయగలను.",
    "kn-IN": "ಈ ಪ್ರಸ್ತುತ ವಿವರವು ಸಹಾಯಕ್ ಎಐ ಜ್ಞಾನ ಭಂಡಾರದಲ್ಲಿ ಇನ್ನೂ ಲಭ್ಯವಿಲ್ಲ. ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿ ಮತ್ತು ಮುಂದಿನ ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ನಾನು ಸಹಾಯ ಮಾಡಬಹುದು.",
    "ml-IN": "ഈ നിലവിലെ വിശദാംശം സഹായക് എഐയുടെ വിജ്ഞാനശേഖരത്തിൽ ഇതുവരെ ലഭ്യമല്ല. നിങ്ങളുടെ സാഹചര്യംയും അടുത്തതായി വേണ്ട രേഖകളും മനസ്സിലാക്കാൻ എനിക്ക് സഹായിക്കാം.",
    "gu-IN": "આ વર્તમાન વિગતો સહાયક એઆઇના જ્ઞાન ભંડારમાં હજી ઉપલબ્ધ નથી. તમારી સ્થિતિ અને આગળ જરૂરી દસ્તાવેજો સમજવામાં હું મદદ કરી શકું છું.",
    "bn-IN": "এই বর্তমান তথ্যটি সহায়ক এআই-এর জ্ঞানভাণ্ডারে এখনও নেই। আপনার অবস্থা এবং পরবর্তী প্রয়োজনীয় নথি বুঝতে আমি সাহায্য করতে পারি।",
    "pa-IN": "ਇਹ ਮੌਜੂਦਾ ਵੇਰਵਾ ਸਹਾਇਕ ਏਆਈ ਦੇ ਗਿਆਨ ਭੰਡਾਰ ਵਿੱਚ ਹਾਲੇ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਤੁਹਾਡੀ ਸਥਿਤੀ ਅਤੇ ਅੱਗੇ ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼ ਸਮਝਣ ਵਿੱਚ ਮੈਂ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ।",
}


def requires_verified_evidence(message: str) -> bool:
    """Classify high-risk/current-information requests conservatively."""

    normalized = message.casefold()
    return any(term in normalized for term in _AUTHORITATIVE_TERMS)


def decide_response(
    *,
    message: str,
    language: str,
    retrieval: RetrievalResult,
    has_reference_document: bool = False,
) -> KnowledgeDecision:
    """Permit Gemini only where an unsupported answer cannot look authoritative."""

    if requires_verified_evidence(message):
        selected = _select_cited_evidence(retrieval)
        if not selected.evidence:
            if has_reference_document:
                # A member's attached document is useful for explanation, but
                # it never becomes an official citation or a claim of current
                # status. The generation prompt makes that boundary explicit.
                return KnowledgeDecision(
                    evidence_status=EvidenceStatus.GENERAL_MODEL_KNOWLEDGE,
                    retrieval=selected,
                    requires_abstention=False,
                )
            return KnowledgeDecision(
                evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                retrieval=selected,
                requires_abstention=True,
                abstention_message=_ABSTENTIONS.get(language, _ABSTENTIONS["en-IN"]),
            )
        status = (
            EvidenceStatus.MULTIPLE_VERIFIED_SOURCES
            if len(selected.citations) > 1
            else EvidenceStatus.VERIFIED_SOURCE
        )
        return KnowledgeDecision(evidence_status=status, retrieval=selected, requires_abstention=False)

    # Dense search always produces neighbours, even for greetings or broad
    # educational conversation. Those neighbours are not evidence used for the
    # answer and must not become a repeated, misleading source list in the UI.
    return KnowledgeDecision(
        evidence_status=EvidenceStatus.GENERAL_MODEL_KNOWLEDGE,
        retrieval=RetrievalResult(unavailable_reason=retrieval.unavailable_reason),
        requires_abstention=False,
    )


def _select_cited_evidence(retrieval: RetrievalResult) -> RetrievalResult:
    """Keep a grounded answer and its visual provenance concise and exact.

    At most two official documents and two chunks per document reach the
    generation prompt.  The same two documents become the only visual links,
    so the UI never displays a long list that the answer did not use.
    """

    selected: list[RetrievedEvidence] = []
    chunks_by_source: dict[tuple[str, str, str | None], int] = {}
    for item in retrieval.evidence:
        source_key = (
            item.citation.source_name,
            item.citation.url,
            item.citation.document_version,
        )
        if source_key not in chunks_by_source and len(chunks_by_source) >= 2:
            continue
        used_chunks = chunks_by_source.get(source_key, 0)
        if used_chunks >= 2:
            continue
        chunks_by_source[source_key] = used_chunks + 1
        selected.append(item)
    return RetrievalResult(evidence=tuple(selected), unavailable_reason=retrieval.unavailable_reason)
