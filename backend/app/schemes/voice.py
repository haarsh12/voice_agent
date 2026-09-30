"""Conservative multilingual scheme-intent handling for voice and chat."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.knowledge.contracts import UserKnowledgeContext
from app.schemes.contracts import SchemeSearchPage
from app.schemes.repository import SchemeRepository


class SchemeIntent(str, Enum):
    FIND_SCHEMES = "FIND_SCHEMES"
    SCHEME_DETAILS = "SCHEME_DETAILS"
    SCHEME_ELIGIBILITY = "SCHEME_ELIGIBILITY"
    SCHEME_BENEFITS = "SCHEME_BENEFITS"
    SCHEME_DOCUMENTS = "SCHEME_DOCUMENTS"
    SCHEME_APPLICATION_PROCESS = "SCHEME_APPLICATION_PROCESS"
    SCHEME_DEADLINE = "SCHEME_DEADLINE"
    SCHEME_STATUS = "SCHEME_STATUS"
    SCHEME_LOCATION = "SCHEME_LOCATION"
    FIND_RELEVANT_SCHEMES = "FIND_RELEVANT_SCHEMES"


_SCHEME_TERMS = (
    "scheme", "schemes", "yojana", "programme", "program", "pmfby", "cpgrams",
    "योजना", "योजने", "स्कीम", "scheme", "योजने", "कर्ज योजना", "विमा",
)
_NEXT_TERMS = ("next", "more", "another", "अगली", "अगले", "आगे", "पुढील", "पुढे", "आणखी")
_INTENT_TERMS: tuple[tuple[SchemeIntent, tuple[str, ...]], ...] = (
    (SchemeIntent.SCHEME_ELIGIBILITY, ("eligible", "eligibility", "पात्र", "पात्रता", "eligible")),
    (SchemeIntent.SCHEME_BENEFITS, ("benefit", "coverage", "premium", "लाभ", "फायदा", "विमा")),
    (SchemeIntent.SCHEME_DOCUMENTS, ("document", "documents", "paper", "दस्तावेज", "कागदपत्र")),
    (SchemeIntent.SCHEME_APPLICATION_PROCESS, ("apply", "application", "register", "आवेदन", "अर्ज")),
    (SchemeIntent.SCHEME_DEADLINE, ("deadline", "last date", "date", "अंतिम तिथि", "मुदत")),
    (SchemeIntent.SCHEME_STATUS, ("status", "open", "closed", "current", "स्थिती", "स्थिति")),
    (SchemeIntent.SCHEME_LOCATION, ("maharashtra", "nagpur", "state", "district", "महाराष्ट्र", "जिल्हा")),
    (SchemeIntent.FIND_RELEVANT_SCHEMES, ("for me", "relevant", "मेरे लिए", "माझ्यासाठी")),
)


@dataclass(frozen=True)
class SchemeVoiceResult:
    intent: SchemeIntent
    page: SchemeSearchPage
    offset: int
    is_next_page: bool


def detect_scheme_intent(message: str) -> SchemeIntent | None:
    normalized = message.casefold()
    if not any(term in normalized for term in _SCHEME_TERMS):
        # Category-only requests must still work after the assistant asks a
        # follow-up, for example “insurance” or “loans”.
        if not any(term in normalized for term in ("farmer", "crop", "insurance", "loan", "cooperative", "pacs", "farmer", "किसान", "शेतकरी", "सहकारी")):
            return None
    for intent, terms in _INTENT_TERMS:
        if any(term in normalized for term in terms):
            return intent
    return SchemeIntent.FIND_SCHEMES


def is_next_page_request(message: str) -> bool:
    normalized = message.casefold().strip()
    return any(re.search(rf"(^|\s){re.escape(term)}(\s|$)", normalized) for term in _NEXT_TERMS)


def voice_filters(message: str, context: UserKnowledgeContext | None) -> tuple[str | None, str | None, str | None, str | None]:
    normalized = message.casefold()
    beneficiary = context.user_type if context else None
    state = context.state if context else None
    district = context.district if context else None
    if any(term in normalized for term in ("farmer", "crop", "किसान", "शेतकरी")):
        beneficiary = "farmer"
    elif "pacs" in normalized:
        beneficiary = "pacs_member"
    elif any(term in normalized for term in ("cooperative", "सहकारी")):
        beneficiary = "cooperative_member"
    if "maharashtra" in normalized or "महाराष्ट्र" in normalized:
        state = "Maharashtra"
    # The deterministic catalogue has no unsupported district assumptions.
    # User profile district remains a ranking/filter input only where a source
    # explicitly supplied district coverage.
    return beneficiary, state, district, message


async def discover_for_voice(
    repository: SchemeRepository,
    *,
    message: str,
    context: UserKnowledgeContext | None,
    offset: int = 0,
) -> SchemeVoiceResult | None:
    intent = detect_scheme_intent(message)
    if intent is None:
        return None
    beneficiary, state, district, query = voice_filters(message, context)
    page = await repository.list_schemes(
        query=query,
        beneficiary=beneficiary,
        state=state,
        district=district,
        limit=3,
        offset=offset,
    )
    return SchemeVoiceResult(intent=intent, page=page, offset=offset, is_next_page=offset > 0)
