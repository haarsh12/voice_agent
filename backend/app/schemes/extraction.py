"""Deterministic, evidence-preserving scheme detection for approved documents.

The extractor deliberately never asks an LLM to fill a missing field.  It
recognises an entity only when its name is stated in an approved document or
is the reviewed name of a dedicated source (for example the PMFBY source).
All descriptive fields remain verbatim bounded excerpts from source chunks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable

from app.knowledge.models import KnowledgeChunk, KnowledgeDocumentVersion, KnowledgeSource

_NAME_SIGNAL = re.compile(
    r"\b(scheme|yojana|programme|program|initiative|mission|fund|facility|insurance|credit|service|support|grievance)\b",
    re.IGNORECASE,
)
_WHITESPACE = re.compile(r"\s+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ExtractedScheme:
    official_name: str
    normalized_name: str
    slug: str
    scheme_type: str
    category: str
    geographic_scope: str
    applicable_states: tuple[str, ...]
    applicable_districts: tuple[str, ...]
    beneficiary_categories: tuple[str, ...]
    relevant_user_types: tuple[str, ...]
    data: dict[str, object]
    evidence_summary: str
    chunk_ids: tuple[str, ...]


def normalize_scheme_name(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip().casefold()


def scheme_slug(value: str) -> str:
    stem = _NON_SLUG.sub("-", normalize_scheme_name(value)).strip("-")[:150] or "official-programme"
    digest = hashlib.sha256(normalize_scheme_name(value).encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}"


def extract_schemes_from_document(
    *,
    source: KnowledgeSource,
    version: KnowledgeDocumentVersion,
    chunks: Iterable[KnowledgeChunk],
) -> tuple[ExtractedScheme, ...]:
    """Return only names supported by the document/source metadata.

    A dedicated official source may identify one programme even where a page
    title is merely "FAQ" or "Guidelines".  Generic sources require an actual
    title or heading with a programme signal, preventing a law, news item, or
    random page from becoming a fake scheme card.
    """

    chunk_list = list(chunks)
    names = _candidate_names(source=source, version=version, chunks=chunk_list)
    extracted: list[ExtractedScheme] = []
    for name in names:
        related = _related_chunks(name, chunk_list)
        if not related:
            related = chunk_list[:1]
        if not related:
            continue
        source_fields = _source_fields(related)
        category = _category(source, version.coverage_categories)
        scheme_type = _scheme_type(source, version.coverage_categories, name)
        beneficiaries = _beneficiaries(source, version.coverage_categories, name)
        data: dict[str, object] = {
            "description": _excerpt(related[0].content),
            "objective": source_fields.get("objective"),
            "eligibility": source_fields.get("eligibility"),
            "benefits": source_fields.get("benefits"),
            "required_documents": source_fields.get("required_documents"),
            "application_process": source_fields.get("application_process"),
            "important_dates": source_fields.get("important_dates"),
            "source_coverage": list(version.coverage_categories),
        }
        # Do not serialise invented empty strings as user-facing data.
        data = {key: value for key, value in data.items() if value not in (None, "", [])}
        extracted.append(
            ExtractedScheme(
                official_name=name,
                normalized_name=normalize_scheme_name(name),
                slug=scheme_slug(name),
                scheme_type=scheme_type,
                category=category,
                geographic_scope=source.geographic_scope,
                applicable_states=_applicable_states(source),
                applicable_districts=(),
                beneficiary_categories=beneficiaries,
                relevant_user_types=beneficiaries,
                data=data,
                evidence_summary=_excerpt(related[0].content, 1_500),
                chunk_ids=tuple(chunk.id for chunk in related[:4]),
            )
        )
    return tuple(extracted)


def _candidate_names(
    *, source: KnowledgeSource, version: KnowledgeDocumentVersion, chunks: list[KnowledgeChunk]
) -> tuple[str, ...]:
    candidates: list[str] = []
    # These reviewed source groups are explicitly named programmes/services;
    # their generic subpages inherit that identity without guessing a name.
    dedicated_names = {
        "pmfby": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "cpgrams": "Centralized Public Grievance Redress and Monitoring System (CPGRAMS)",
        "pm_kisan": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "kisan_credit_card": "Kisan Credit Card (KCC)",
        "agriculture_infrastructure_fund": "Agriculture Infrastructure Fund (AIF)",
        "pmksy": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
        "soil_health_card": "Soil Health Card Scheme",
        "paramparagat_krishi_vikas": "Paramparagat Krishi Vikas Yojana (PKVY)",
        "sub_mission_agricultural_mechanization": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "horticulture_mission": "Mission for Integrated Development of Horticulture (MIDH)",
        "e_nam": "National Agriculture Market (e-NAM)",
        "minimum_support_price": "Minimum Support Price (MSP)",
    }
    if source.key in dedicated_names:
        # A dedicated programme portal can have titles such as FAQ, Help, or
        # Crop Insurance. One canonical entity avoids duplicate cards for
        # every page title from the same programme.
        return (dedicated_names[source.key],)
    for raw in [version.title, *(chunk.heading or "" for chunk in chunks)]:
        cleaned = _clean_title(raw)
        extracted_name = _programme_name_from_announcement(cleaned) if cleaned and _is_announcement_title(cleaned) else None
        if extracted_name:
            candidates.append(extracted_name)
        elif cleaned and _NAME_SIGNAL.search(cleaned) and not _is_announcement_title(cleaned):
            candidates.append(cleaned)
    unique: dict[str, str] = {}
    for candidate in candidates:
        # Headings that are only a generic field describe a programme but do
        # not name one, and must never become catalogue entities.
        if len(candidate) >= 4 and candidate.casefold() not in {
            "eligibility", "benefits", "documents", "application process", "guidelines", "faq",
        }:
            unique.setdefault(normalize_scheme_name(candidate), candidate[:500])
    return tuple(unique.values())


def _clean_title(value: str) -> str:
    value = _WHITESPACE.sub(" ", value).strip(" -:|·\t\r\n")
    return value[:500]


def _is_announcement_title(value: str) -> bool:
    """Avoid turning a press-event headline into a programme name."""

    normalized = value.casefold()
    return normalized.startswith(
        (
            "union minister ",
            "minister ",
            "mos ",
            "launch of ",
            "cabinet ",
            "press release",
            "media release",
        )
    )


def _programme_name_from_announcement(value: str) -> str | None:
    """Keep an explicitly named programme, never the surrounding headline."""

    patterns = (
        r"^cabinet approves the (?P<name>.+?)(?: under |$)",
        r"(?:scheme of|scheme )['“](?P<name>[^'”]{4,180})['”]",
    )
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            candidate = _clean_title(match.group("name"))
            if _NAME_SIGNAL.search(candidate):
                return candidate
    return None


def _related_chunks(name: str, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
    tokens = {term for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", name.casefold()) if term not in _signal_terms()}
    related = [chunk for chunk in chunks if not tokens or any(term in chunk.content.casefold() for term in tokens)]
    return related or chunks[:1]


def _source_fields(chunks: list[KnowledgeChunk]) -> dict[str, str]:
    labels = {
        "eligibility": ("eligib", "who can", "beneficiar", "पात्र"),
        "benefits": ("benefit", "coverage", "assistance", "premium", "लाभ"),
        "required_documents": ("document", "certificate", "identity", "दस्तावेज"),
        "application_process": ("apply", "application", "register", "आवेदन"),
        "important_dates": ("deadline", "last date", "date", "timeline", "समय सीमा"),
        "objective": ("objective", "purpose", "aim", "उद्देश्य"),
    }
    values: dict[str, str] = {}
    for field, signals in labels.items():
        for chunk in chunks:
            heading = (chunk.heading or "").casefold()
            content = chunk.content.casefold()
            if any(signal in heading or signal in content for signal in signals):
                values[field] = _excerpt(chunk.content)
                break
    return values


def _category(source: KnowledgeSource, coverage: list[str]) -> str:
    values = " ".join([source.category, *coverage]).casefold()
    if "insurance" in values or "fasal bima" in values:
        return "Crop insurance"
    if "grievance" in values or "appeal" in values or "cpgrams" in values:
        return "Government services"
    if "pacs" in values or "cooperative" in values or "ncdc" in values or "sahakar" in values:
        return "Cooperatives"
    if "credit" in values or "financial" in values or "bank" in values or "kcc" in values or "loan" in values:
        return "Financial inclusion"
    if "fisheries" in values or "pmmsy" in values or "aquaculture" in values or "fidf" in values:
        return "Fisheries"
    if "dairy" in values or "livestock" in values or "gokul" in values or "animal husbandry" in values or "poultry" in values:
        return "Livestock & Dairy"
    if "food processing" in values or "pmfme" in values or "sampada" in values or "cold chain" in values:
        return "Food processing"
    if "tribal" in values or "van dhan" in values or "mfp" in values or "trifed" in values:
        return "Tribal welfare"
    if "fpo" in values or "farmer producer" in values or "producer organisation" in values:
        return "Farmer Producer Organisations"
    if "irrigation" in values or "pmksy" in values or "sinchayee" in values or "watershed" in values:
        return "Irrigation"
    if "soil health" in values or "soil testing" in values or "nutrient" in values:
        return "Soil health"
    if "organic" in values or "pkvy" in values or "paramparagat" in values:
        return "Organic farming"
    if "mechanization" in values or "smam" in values or "machinery" in values or "chc" in values:
        return "Agricultural mechanization"
    if "horticulture" in values or "midh" in values:
        return "Horticulture"
    if "marketing" in values or "e-nam" in values or "mandi" in values or "agmarknet" in values:
        return "Agricultural marketing"
    if "msp" in values or "procurement" in values or "minimum support price" in values:
        return "Procurement"
    if "pm-kisan" in values or "pm kisan" in values or "income support" in values:
        return "Income support"
    if "infrastructure" in values or "aif" in values or "agri infra" in values:
        return "Infrastructure financing"
    if "agri" in values or "farmer" in values or "crop" in values or "krishi" in values:
        return "Agriculture"
    if source.geographic_scope == "STATE":
        return "State-specific"
    return "Government services"


def _scheme_type(source: KnowledgeSource, coverage: list[str], name: str) -> str:
    values = " ".join([source.category, *coverage, name]).casefold()
    if "insurance" in values or "bima" in values:
        return "INSURANCE"
    if "grievance" in values or "appeal" in values or "complaint" in values:
        return "GRIEVANCE_SERVICE"
    if "credit" in values or "loan" in values or "kcc" in values or "financing" in values:
        return "CREDIT_FACILITY"
    if "fund" in values or "aif" in values or "fidf" in values:
        return "FINANCING_FACILITY"
    if "mission" in values or "abhiyan" in values:
        return "MISSION"
    if "yojana" in values or "scheme" in values or "programme" in values:
        return "PROGRAMME"
    if "initiative" in values or "vikas" in values or "development" in values:
        return "INITIATIVE"
    if "service" in values or "registration" in values or "portal" in values or "e-nam" in values:
        return "SERVICE"
    if "subsidy" in values or "assistance" in values or "support" in values:
        return "SUBSIDY_SCHEME"
    if "msp" in values or "procurement" in values:
        return "PROCUREMENT_SCHEME"
    return "PROGRAMME"


def _beneficiaries(source: KnowledgeSource, coverage: list[str], name: str) -> tuple[str, ...]:
    values = " ".join([source.category, *coverage, name]).casefold()
    result: list[str] = []
    if any(token in values for token in ("agri", "farmer", "crop", "pmfby", "pm-kisan", "kisan", "shetkari", "krishi")):
        result.append("farmer")
    if "pacs" in values:
        result.append("pacs_member")
    if any(token in values for token in ("cooperative", "ncdc", "sahakar", "sahakari")):
        result.extend(("cooperative_member", "cooperative_official"))
    if any(token in values for token in ("fisheries", "pmmsy", "fisherman", "aquaculture", "matsya")):
        result.append("fisheries_stakeholder")
    if any(token in values for token in ("dairy", "milk", "livestock", "gokul", "animal husbandry", "doodh", "pashupalan")):
        result.append("dairy_livestock_farmer")
    if any(token in values for token in ("food processing", "pmfme", "food entrepreneur", "micro enterprise")):
        result.append("food_entrepreneur")
    if any(token in values for token in ("tribal", "van dhan", "adivasi", "mfp", "forest produce")):
        result.append("tribal_community")
    if any(token in values for token in ("fpo", "farmer producer", "producer organisation")):
        result.append("fpo_member")
    if any(token in values for token in ("women", "mahila", "self help", "shg")):
        result.append("women")
    if any(token in values for token in ("youth", "yuva", "young", "student")):
        result.append("youth")
    if any(token in values for token in ("small", "marginal", "landless", "tenant")):
        result.append("small_marginal_farmer")
    if not result and ("rural" in values or source.geographic_scope in {"NATIONAL", "STATE"}):
        result.append("rural_stakeholder")
    return tuple(dict.fromkeys(result))


def _applicable_states(source: KnowledgeSource) -> tuple[str, ...]:
    """Use only reviewed source scope, never a model guess from a URL/text."""

    # The source registry explicitly approves Maharashtra as the first State
    # RCS coverage.  Additional state sources must be added to that registry
    # before this mapping can expand.
    state_mapping = {
        "state_rcs": ("Maharashtra",),
        "maharashtra_agriculture": ("Maharashtra",),
    }
    return state_mapping.get(source.key, ())


def _excerpt(value: str, limit: int = 900) -> str:
    return _WHITESPACE.sub(" ", value).strip()[:limit]


def _signal_terms() -> set[str]:
    return {"scheme", "yojana", "programme", "program", "initiative", "mission", "fund", "facility", "insurance", "credit", "service", "support", "grievance"}
