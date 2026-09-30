"""Trusted, configuration-like routing catalogue for grievance handoffs.

Natural-language models may help collect facts, but they never decide a
government destination.  The small catalogue below is deliberately explicit
and only exposes the official CPGRAMS citizen and status pages.  It can be
moved to a reviewed authority table/configuration service later without
changing grievance lifecycle code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GrievanceCategory(StrEnum):
    PACS = "PACS_ISSUE"
    COOPERATIVE = "COOPERATIVE_SOCIETY"
    PAYMENT = "PAYMENT"
    LOAN = "LOAN"
    INSURANCE = "INSURANCE_CLAIM"
    SCHEME = "GOVERNMENT_SCHEME"
    AGRICULTURE = "AGRICULTURE_SERVICE"
    FINANCIAL_SERVICE = "FINANCIAL_SERVICE"
    DOCUMENT = "DOCUMENT_CERTIFICATE"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    OTHER = "OTHER_GOVERNMENT"


@dataclass(frozen=True)
class TrustedRoute:
    key: str
    authority_name: str
    destination_name: str
    destination_url: str
    tracking_url: str
    reason: str


# Verified 2026-09-30 against the Government of India's CPGRAMS pages:
# https://www.pgportal.gov.in/ and https://pgportal.gov.in/Status
# CPGRAMS states it accepts grievances for Central/State Government bodies and
# provides a registration ID for status tracking.  It remains a handoff: the
# citizen chooses the specific authority in the official portal.
_CPGRAMS_CITIZEN_URL = "https://www.pgportal.gov.in/Home/LodgeGrievance"
_CPGRAMS_STATUS_URL = "https://pgportal.gov.in/Status"

_ROUTES: dict[GrievanceCategory, TrustedRoute] = {
    GrievanceCategory.PACS: TrustedRoute(
        key="cpgrams-cooperative",
        authority_name="Appropriate cooperative authority",
        destination_name="CPGRAMS — select the relevant cooperative authority",
        destination_url=_CPGRAMS_CITIZEN_URL,
        tracking_url=_CPGRAMS_STATUS_URL,
        reason="PACS and cooperative service concerns need the competent cooperative authority selected by the member in CPGRAMS.",
    ),
    GrievanceCategory.COOPERATIVE: TrustedRoute(
        key="cpgrams-cooperative",
        authority_name="Appropriate cooperative authority",
        destination_name="CPGRAMS — select the relevant cooperative authority",
        destination_url=_CPGRAMS_CITIZEN_URL,
        tracking_url=_CPGRAMS_STATUS_URL,
        reason="The official CPGRAMS handoff lets the member select the competent Central or State cooperative authority.",
    ),
}

_DEFAULT_ROUTE = TrustedRoute(
    key="cpgrams-citizen",
    authority_name="Appropriate public authority",
    destination_name="CPGRAMS — select the responsible authority",
    destination_url=_CPGRAMS_CITIZEN_URL,
    tracking_url=_CPGRAMS_STATUS_URL,
    reason="CPGRAMS is the verified citizen handoff; the member must select the responsible Central or State authority there.",
)


def route_for(category: GrievanceCategory) -> TrustedRoute:
    """Return a destination only from this reviewed catalogue."""

    return _ROUTES.get(category, _DEFAULT_ROUTE)


def classify_statement(statement: str) -> GrievanceCategory:
    """Conservative keyword classification for a draft suggestion.

    This is intentionally a convenience only.  The member can always choose
    another category, and no category selection changes the official route
    outside the trusted registry.
    """

    text = statement.casefold()
    keyword_groups: tuple[tuple[GrievanceCategory, tuple[str, ...]], ...] = (
        (GrievanceCategory.INSURANCE, ("insurance", "claim", "pmfby", "बीमा", "फसल बीमा", "दावा")),
        (GrievanceCategory.LOAN, ("loan", "credit", "ऋण", "कर्ज")),
        (GrievanceCategory.PAYMENT, ("payment", "paid", "money", "salary", "पैसा", "भुगतान", "पेमेंट")),
        (GrievanceCategory.PACS, ("pacs", "पीएसीएस")),
        (GrievanceCategory.COOPERATIVE, ("cooperative", "society", "सहकारी", "सोसाइटी")),
        (GrievanceCategory.DOCUMENT, ("certificate", "document", "प्रमाणपत्र", "दस्तावेज")),
        (GrievanceCategory.SCHEME, ("scheme", "yojana", "योजना")),
        (GrievanceCategory.AGRICULTURE, ("farmer", "crop", "agriculture", "किसान", "फसल", "कृषि")),
    )
    for category, keywords in keyword_groups:
        if any(keyword in text for keyword in keywords):
            return category
    return GrievanceCategory.OTHER
