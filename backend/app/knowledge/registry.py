"""The only initial allowlist of sources eligible for verified ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class ApprovedSourceDefinition:
    """Configuration for a source group, not a fetched document or citation."""

    key: str
    name: str
    category: str
    authority_level: int
    geographic_scope: str
    check_interval_hours: int
    approved_domains: tuple[str, ...]
    entry_urls: tuple[str, ...]
    # Discovery is intentionally one-hop and path-scoped.  A source page may
    # link to third-party material, campaign pages, or unreviewed applications;
    # none become ingestible unless their path is listed here.
    discovery_path_prefixes: tuple[str, ...] = ()
    max_documents_per_check: int = 25
    enabled: bool = True


# This deliberately starts with exactly the ten source groups approved for the
# product. New domains must go through a reviewed registry change rather than
# being inferred from a user question, search result, redirect, or LLM output.
SOURCE_REGISTRY: tuple[ApprovedSourceDefinition, ...] = (
    ApprovedSourceDefinition(
        key="ministry_of_cooperation",
        name="Ministry of Cooperation",
        category="cooperative_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("cooperation.gov.in",),
        entry_urls=("https://www.cooperation.gov.in/en/homepage",),
        discovery_path_prefixes=("/sites/default/files/", "/en/notices", "/en/circular", "/en/acts", "/en/rules", "/en/schemes"),
    ),
    ApprovedSourceDefinition(
        key="national_cooperative_database",
        name="National Cooperative Database",
        category="cooperative_data",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24 * 7,
        approved_domains=("cooperatives.gov.in",),
        entry_urls=("https://cooperatives.gov.in/",),
        discovery_path_prefixes=("/documents/", "/files/", "/sites/default/files/"),
    ),
    ApprovedSourceDefinition(
        key="central_registrar_of_cooperative_societies",
        name="CRCS — Central Registrar of Cooperative Societies",
        category="cooperative_regulation",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("crcs.gov.in",),
        entry_urls=("https://crcs.gov.in/public/",),
        discovery_path_prefixes=("/public/",),
    ),
    ApprovedSourceDefinition(
        key="india_code",
        name="India Code",
        category="law_and_regulation",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24 * 7,
        approved_domains=("indiacode.gov.in", "indiacode.nic.in"),
        entry_urls=("https://indiacode.gov.in/",),
        discovery_path_prefixes=("/handle/", "/bitstream/", "/show-data"),
    ),
    ApprovedSourceDefinition(
        key="state_rcs",
        name="State RCS / State Cooperative Department",
        category="state_cooperative_regulation",
        authority_level=95,
        geographic_scope="STATE",
        check_interval_hours=24,
        # Initial discovery starts from the CRCS state-registrar directory.
        # Individual state domains must be explicitly added after review.
        approved_domains=("crcs.gov.in",),
        entry_urls=("https://crcs.gov.in/state_registrar",),
        discovery_path_prefixes=("/state_registrar",),
    ),
    ApprovedSourceDefinition(
        key="pmfby",
        name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        category="crop_insurance",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pmfby.gov.in",),
        entry_urls=("https://pmfby.gov.in/",),
        discovery_path_prefixes=("/documents/", "/pdf/", "/guideline", "/circular", "/notification"),
    ),
    ApprovedSourceDefinition(
        key="ministry_of_agriculture",
        name="Ministry of Agriculture & Farmers Welfare",
        category="agriculture_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("agriwelfare.gov.in",),
        entry_urls=("https://agriwelfare.gov.in/",),
        discovery_path_prefixes=("/documents/", "/sites/default/files/", "/files/"),
    ),
    ApprovedSourceDefinition(
        key="myscheme",
        name="myScheme",
        category="scheme_discovery",
        authority_level=90,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("myscheme.gov.in",),
        entry_urls=("https://www.myscheme.gov.in/",),
        discovery_path_prefixes=("/schemes/",),
    ),
    ApprovedSourceDefinition(
        key="reserve_bank_of_india",
        name="Reserve Bank of India",
        category="financial_literacy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("rbi.org.in",),
        entry_urls=("https://www.rbi.org.in/",),
        discovery_path_prefixes=("/documents/", "/scripts/", "/commonman/", "/notification"),
    ),
    ApprovedSourceDefinition(
        key="cpgrams",
        name="CPGRAMS",
        category="public_grievances",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pgportal.gov.in",),
        entry_urls=("https://pgportal.gov.in/",),
        discovery_path_prefixes=("/Home/Preview/", "/docs/", "/files/"),
    ),
)

SOURCES_BY_KEY = {source.key: source for source in SOURCE_REGISTRY}


def canonicalize_url(url: str) -> str:
    """Normalize a source URL without weakening its origin or query semantics."""

    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    try:
        port_number = parsed.port
    except ValueError as error:
        raise ValueError("source URL has an invalid port") from error
    port = f":{port_number}" if port_number and port_number != 443 else ""
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), f"{host}{port}", path, parsed.query, ""))


def is_approved_source_url(url: str, source: ApprovedSourceDefinition) -> bool:
    """Reject arbitrary destinations before every fetch and citation render."""

    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        is_default_https_port = parsed.port in {None, 443}
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(host)
        and parsed.username is None
        and parsed.password is None
        and is_default_https_port
        and any(host == domain or host.endswith(f".{domain}") for domain in source.approved_domains)
    )
