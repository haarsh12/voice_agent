"""Small, reviewed catalogue of official references shown with text replies.

This is deliberately an allowlist, not a model-generated citation system. It
keeps links trustworthy until a full retrieval and ingestion pipeline is added.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialSource:
    key: str
    name: str
    url: str
    terms: tuple[str, ...]


OFFICIAL_SOURCES: tuple[OfficialSource, ...] = (
    OfficialSource(
        key="pmfby",
        name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        url="https://pmfby.gov.in/",
        terms=("pmfby", "fasal bima", "crop insurance", "फसल बीमा", "प्रधानमंत्री फसल बीमा", "पीएमएफबीवाई"),
    ),
    OfficialSource(
        key="pacs",
        name="Ministry of Cooperation — About PACS",
        url="https://www.cooperation.gov.in/en/about-primary-agriculture-cooperative-credit-societies-pacs",
        terms=("pacs", "primary agricultural credit", "primary agriculture credit", "पैक्स", "प्राथमिक कृषि", "credit society"),
    ),
    OfficialSource(
        key="cooperation",
        name="Ministry of Cooperation, Government of India",
        url="https://www.cooperation.gov.in/en/homepage",
        terms=("cooperative", "co-operative", "cooperation", "by-law", "bye-law", "member", "society", "सहकारी", "सहकारिता", "उपनियम", "सदस्य"),
    ),
    OfficialSource(
        key="agriculture",
        name="Ministry of Agriculture & Farmers Welfare",
        url="https://agriwelfare.gov.in/",
        terms=("farmer", "agriculture", "crop", "kisan", "किसान", "कृषि", "खेती", "फसल"),
    ),
    OfficialSource(
        key="financial",
        name="Reserve Bank of India — Financial Education",
        url="https://www.rbi.org.in/",
        terms=("bank", "banking", "loan", "saving", "interest", "upi", "digital payment", "financial", "credit", "बैंक", "ऋण", "बचत", "ब्याज", "वित्त", "भुगतान"),
    ),
    OfficialSource(
        key="grievance",
        name="CPGRAMS — Public Grievance Portal",
        url="https://pgportal.gov.in/",
        terms=("grievance", "complaint", "redressal", "complain", "शिकायत", "निवारण", "निपटान"),
    ),
)

_DEFAULT_SOURCE = next(source for source in OFFICIAL_SOURCES if source.key == "cooperation")


def select_official_sources(message: str, *, limit: int = 2) -> tuple[OfficialSource, ...]:
    """Return at most two relevant, reviewed government references.

    The user's text drives selection. The model never chooses a URL, so it
    cannot fabricate or redirect the user to an untrusted site.
    """

    query = message.casefold()
    selected = [source for source in OFFICIAL_SOURCES if any(term in query for term in source.terms)]
    if not selected:
        return (_DEFAULT_SOURCE,)
    return tuple(selected[:limit])


def source_catalogue_summary() -> str:
    """A compact source-domain reminder suitable for a model instruction."""

    return ", ".join(source.url for source in OFFICIAL_SOURCES)
