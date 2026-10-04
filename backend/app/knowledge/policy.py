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
    "hi-IN": "मैं इसके बारे में सामान्य जानकारी दे सकती हूँ। आमतौर पर सरकार किसानों के लिए विभिन्न योजनाएं चलाती है। क्या आप कोई विशेष विवरण जानना चाहते हैं?",
    "mr-IN": "मी याबद्दल सामान्य माहिती देऊ शकते. सामान्यपणे सरकार शेतकऱ्यांसाठी विविध योजना चालवते. तुम्हाला काही विशिष्ट तपशील हवेत का?",
    "en-IN": "That current detail is not yet available in Sahayak AI. I can provide general information about it; would you like a general explanation?",
    "ta-IN": "இதைப் பற்றி பொதுவான தகவலை வழங்க முடியும். பொதுவாக அரசாங்கம் விவசாயிகளுக்காக பல்வேறு திட்டங்களை நடத்துகிறது. ஏதேனும் குறிப்பிட்ட விவரங்கள் தேவையா?",
    "te-IN": "నేను దీని గురించి సాధారణ సమాచారం అందించగలను. సాధారణంగా ప్రభుత్వం రైతుల కోసం వివిధ పథకాలను నడుపుతుంది. ఏదైనా నిర్దిష్ట వివరాలు కావాలా?",
    "kn-IN": "ನಾನು ಇದರ ಬಗ್ಗೆ ಸಾಮಾನ್ಯ ಮಾಹಿತಿಯನ್ನು ನೀಡಬಲ್ಲೆ. ಸಾಮಾನ್ಯವಾಗಿ ಸರ್ಕಾರವು ರೈತರಿಗಾಗಿ ವಿವಿಧ ಯೋಜನೆಗಳನ್ನು ನಡೆಸುತ್ತದೆ. ಯಾವುದಾದರೂ ನಿರ್ದಿಷ್ಟ ವಿವರಗಳು ಬೇಕೇ?",
    "ml-IN": "എനിക്ക് ഇതേക്കുറിച്ച് പൊതുവായ വിവരങ്ങൾ നൽകാം. സാധാരണയായി സർക്കാർ കർഷകർക്കായി വിവിധ പദ്ധതികൾ നടപ്പിലാക്കുന്നു. എന്തെങ്കിലും പ്രത്യേക വിശദാംശങ്ങൾ വേണോ?",
    "gu-IN": "હું આ વિશે સામાન્ય માહિતી આપી શકું છું. સામાન્ય રીતે સરકાર ખેડૂતો માટે વિવિધ યોજનાઓ ચલાવે છે. શું તમને કોઈ ચોક્કસ વિગતો જોઈએ છે?",
    "bn-IN": "আমি এই বিষয়ে সাধারণ তথ্য দিতে পারি। সাধারণত সরকার কৃষকদের জন্য বিভিন্ন প্রকল্প পরিচালনা করে। আপনি কি কোনো নির্দিষ্ট বিবরণ জানতে চান?",
    "pa-IN": "ਮੈਂ ਇਸ ਬਾਰੇ ਆਮ ਜਾਣਕਾਰੀ ਦੇ ਸਕਦੀ ਹਾਂ। ਆਮ ਤੌਰ 'ਤੇ ਸਰਕਾਰ ਕਿਸਾਨਾਂ ਲਈ ਵੱਖ-ਵੱਖ ਯੋਜਨਾਵਾਂ ਚਲਾਉਂਦੀ ਹੈ। ਕੀ ਤੁਹਾਨੂੰ ਕੋਈ ਖਾਸ ਵੇਰਵੇ ਚਾਹੀਦੇ ਹਨ?",
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
