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
    "hi-IN": "मैं उपलब्ध आधिकारिक स्रोतों से इस जानकारी की वर्तमान स्थिति सत्यापित नहीं कर सका/सकी। कृपया आधिकारिक पोर्टल से जांचें।",
    "mr-IN": "उपलब्ध अधिकृत स्रोतांतून ही माहिती सध्या पडताळता आली नाही. कृपया अधिकृत पोर्टलवर तपासा.",
    "en-IN": "I could not verify the current information from the available official sources. Please check the relevant official portal.",
    "ta-IN": "கிடைக்கக்கூடிய அதிகாரப்பூர்வ ஆதாரங்களில் இந்தத் தகவலை தற்போது சரிபார்க்க முடியவில்லை. அதிகாரப்பூர்வ தளத்தில் பார்க்கவும்.",
    "te-IN": "అందుబాటులో ఉన్న అధికారిక మూలాల నుండి ఈ సమాచారాన్ని ప్రస్తుతం ధృవీకరించలేకపోయాను. దయచేసి అధికారిక పోర్టల్‌ను చూడండి.",
    "kn-IN": "ಲಭ್ಯವಿರುವ ಅಧಿಕೃತ ಮೂಲಗಳಿಂದ ಈ ಮಾಹಿತಿಯನ್ನು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ಪರಿಶೀಲಿಸಿ.",
    "ml-IN": "ലഭ്യമായ ഔദ്യോഗിക സ്രോതസുകളിൽ നിന്ന് ഈ വിവരം ഇപ്പോൾ സ്ഥിരീകരിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി ഔദ്യോഗിക പോർട്ടൽ പരിശോധിക്കുക.",
    "gu-IN": "ઉપલબ્ધ સત્તાવાર સ્ત્રોતોમાંથી આ માહિતી હાલમાં ચકાસી શકાઈ નથી. કૃપા કરીને સત્તાવાર પોર્ટલ તપાસો.",
    "bn-IN": "উপলব্ধ সরকারি উৎস থেকে এই তথ্যটি বর্তমানে যাচাই করা যায়নি। অনুগ্রহ করে সংশ্লিষ্ট সরকারি পোর্টাল দেখুন।",
    "pa-IN": "ਉਪਲਬਧ ਅਧਿਕਾਰਤ ਸਰੋਤਾਂ ਤੋਂ ਇਸ ਜਾਣਕਾਰੀ ਦੀ ਮੌਜੂਦਾ ਸਥਿਤੀ ਦੀ ਪੁਸ਼ਟੀ ਨਹੀਂ ਹੋ ਸਕੀ। ਕਿਰਪਾ ਕਰਕੇ ਅਧਿਕਾਰਤ ਪੋਰਟਲ ਵੇਖੋ।",
}


def requires_verified_evidence(message: str) -> bool:
    """Classify high-risk/current-information requests conservatively."""

    normalized = message.casefold()
    return any(term in normalized for term in _AUTHORITATIVE_TERMS)


def decide_response(*, message: str, language: str, retrieval: RetrievalResult) -> KnowledgeDecision:
    """Permit Gemini only where an unsupported answer cannot look authoritative."""

    if requires_verified_evidence(message):
        selected = _select_cited_evidence(retrieval)
        if not selected.evidence:
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
