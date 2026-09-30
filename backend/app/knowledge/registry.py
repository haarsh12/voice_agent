"""The only initial allowlist of sources eligible for verified ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class CrawlTarget:
    """One reviewed entry point and the PS knowledge it is expected to cover."""

    url: str
    categories: tuple[str, ...]


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
    crawl_targets: tuple[CrawlTarget, ...]
    expected_categories: tuple[str, ...]
    # Discovery is intentionally one-hop and path-scoped.  A source page may
    # link to third-party material, campaign pages, or unreviewed applications;
    # none become ingestible unless their path is listed here.
    discovery_path_prefixes: tuple[str, ...] = ()
    max_documents_per_check: int = 25
    enabled: bool = True

    @property
    def entry_urls(self) -> tuple[str, ...]:
        """Compatibility boundary for the database and checked worker code."""

        return tuple(target.url for target in self.crawl_targets)

    def categories_for_entry_url(self, url: str) -> tuple[str, ...]:
        """Keep discovery coverage attributable to the reviewed parent target."""

        canonical = canonicalize_url(url)
        for target in self.crawl_targets:
            if canonicalize_url(target.url) == canonical:
                return target.categories
        return ()


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
        crawl_targets=(
            CrawlTarget("https://www.cooperation.gov.in/en", ("cooperative_policy", "official_announcements")),
            CrawlTarget("https://www.cooperation.gov.in/en/notices-circulars", ("notifications", "circulars")),
            CrawlTarget("https://www.cooperation.gov.in/en/pacs-related-schemes", ("pacs_initiatives", "schemes")),
            CrawlTarget("https://www.cooperation.gov.in/en/initiatives-ministry-cooperation", ("cooperative_policy", "pacs_initiatives")),
            CrawlTarget("https://www.cooperation.gov.in/en/computerization-pacs", ("pacs_initiatives", "guidelines")),
        ),
        expected_categories=("cooperative_policy", "schemes", "pacs_initiatives", "notifications", "circulars", "guidelines"),
        discovery_path_prefixes=("/sites/default/files/", "/en/notices", "/en/circular", "/en/acts", "/en/rules", "/en/schemes", "/en/pacs", "/en/initiatives"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="national_cooperative_database",
        name="National Cooperative Database",
        category="cooperative_data",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24 * 7,
        approved_domains=("cooperatives.gov.in", "cooperation.gov.in"),
        crawl_targets=(
            CrawlTarget("https://cooperatives.gov.in/", ("cooperative_directory", "cooperative_statistics", "geographic_cooperative_data")),
            CrawlTarget("https://www.cooperation.gov.in/sites/default/files/2024-03/Final_National_Cooperative_Database_023.pdf", ("cooperative_statistics", "geographic_cooperative_data", "pacs_information")),
        ),
        expected_categories=("cooperative_directory", "cooperative_statistics", "geographic_cooperative_data", "pacs_information"),
        discovery_path_prefixes=("/documents/", "/files/", "/sites/default/files/", "/sites/default/files/2024-03/"),
    ),
    ApprovedSourceDefinition(
        key="central_registrar_of_cooperative_societies",
        name="CRCS — Central Registrar of Cooperative Societies",
        category="cooperative_regulation",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("crcs.gov.in",),
        crawl_targets=(
            CrawlTarget("https://crcs.gov.in/public/", ("registration_services", "member_services", "grievance_information")),
            CrawlTarget("https://crcs.gov.in/public/ombuds-notification", ("notifications", "grievance_information")),
            CrawlTarget("https://crcs.gov.in/public/view-all-notification", ("notifications", "circulars")),
            CrawlTarget("https://crcs.gov.in/public/landing/images/Rules2002.pdf", ("rules", "cooperative_regulation")),
        ),
        expected_categories=("cooperative_regulation", "rules", "registration_services", "member_services", "notifications", "circulars", "grievance_information"),
        discovery_path_prefixes=("/public/",),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="india_code",
        name="India Code",
        category="law_and_regulation",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24 * 7,
        approved_domains=("indiacode.gov.in", "indiacode.nic.in"),
        crawl_targets=(
            CrawlTarget("https://indiacode.gov.in/", ("legal_repository",)),
            CrawlTarget("https://www.indiacode.nic.in/bitstream/123456789/1914/1/aA2002-39.pdf", ("multi_state_cooperative_societies_act", "cooperative_law", "relevant_rules")),
        ),
        expected_categories=("legal_repository", "cooperative_law", "multi_state_cooperative_societies_act", "relevant_rules"),
        discovery_path_prefixes=("/handle/", "/bitstream/", "/show-data"),
    ),
    ApprovedSourceDefinition(
        key="state_rcs",
        name="State RCS / State Cooperative Department",
        category="state_cooperative_regulation",
        authority_level=95,
        geographic_scope="STATE",
        check_interval_hours=24,
        # Maharashtra is the reviewed first state. More state domains require
        # an explicit registry review rather than following CRCS outbound links.
        approved_domains=("mahasahakar.maharashtra.gov.in",),
        crawl_targets=(
            CrawlTarget("https://mahasahakar.maharashtra.gov.in/en/", ("state_cooperative_information", "official_contacts")),
            CrawlTarget("https://mahasahakar.maharashtra.gov.in/en/document-category/acts-rules/", ("maharashtra_cooperative_law", "state_rules")),
            CrawlTarget("https://mahasahakar.maharashtra.gov.in/en/document-category/circulars-standing-orders/", ("state_circulars", "state_notifications")),
        ),
        expected_categories=("state_cooperative_information", "maharashtra_cooperative_law", "state_rules", "state_circulars", "state_notifications", "official_contacts"),
        discovery_path_prefixes=("/en/document/", "/en/document-category/", "/sites/default/files/"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="pmfby",
        name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        category="crop_insurance",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pmfby.gov.in",),
        crawl_targets=(
            CrawlTarget("https://pmfby.gov.in/", ("scheme_overview", "current_operational_information", "claim_information", "crops")),
            CrawlTarget("https://pmfby.gov.in/faq", ("faqs", "eligibility", "premium", "coverage", "claims")),
            CrawlTarget("https://pmfby.gov.in/help", ("application_process", "claim_information", "official_contacts")),
            CrawlTarget("https://pmfby.gov.in/pdf/Revamped%20Operational%20Guidelines_17th%20August%202020.pdf", ("operational_guidelines", "claims", "loss_reporting", "deadlines")),
        ),
        expected_categories=("scheme_overview", "eligibility", "crops", "coverage", "premium", "claims", "loss_reporting", "deadlines", "operational_guidelines", "faqs", "current_operational_information"),
        discovery_path_prefixes=("/documents/", "/pdf/", "/guideline", "/circular", "/notification", "/faq", "/help"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="ministry_of_agriculture",
        name="Ministry of Agriculture & Farmers Welfare",
        category="agriculture_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("agriwelfare.gov.in",),
        crawl_targets=(
            CrawlTarget("https://agriwelfare.gov.in/", ("agriculture_policy", "farmer_programs")),
            CrawlTarget("https://agriwelfare.gov.in/en", ("agriculture_schemes", "farmer_programs", "official_announcements", "guidelines", "notifications")),
        ),
        expected_categories=("agriculture_schemes", "agriculture_policy", "farmer_programs", "guidelines", "notifications", "official_announcements"),
        discovery_path_prefixes=("/documents/", "/sites/default/files/", "/files/", "/en/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="myscheme",
        name="myScheme",
        category="scheme_discovery",
        authority_level=90,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("myscheme.gov.in",),
        crawl_targets=(
            CrawlTarget("https://www.myscheme.gov.in/about", ("scheme_discovery", "eligibility_guidance", "application_guidance")),
            CrawlTarget("https://www.myscheme.gov.in/search", ("central_schemes", "state_schemes")),
            CrawlTarget("https://www.myscheme.gov.in/search/state/all-states", ("state_schemes", "maharashtra_schemes")),
        ),
        expected_categories=("scheme_discovery", "central_schemes", "state_schemes", "maharashtra_schemes", "eligibility_guidance", "application_guidance"),
        discovery_path_prefixes=("/schemes/", "/search/"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="reserve_bank_of_india",
        name="Reserve Bank of India",
        category="financial_literacy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("rbi.org.in",),
        crawl_targets=(
            CrawlTarget("https://www.rbi.org.in/commonman/English/Scripts/fame.aspx", ("financial_literacy", "consumer_awareness", "digital_financial_safety")),
            CrawlTarget("https://www.rbi.org.in/Commonman/English/Scripts/FAQs.aspx", ("banking_basics", "consumer_protection", "cooperative_banking")),
            CrawlTarget("https://www.rbi.org.in/commonperson/images/FAME202426022024.pdf", ("financial_literacy", "responsible_borrowing", "complaint_guidance")),
        ),
        expected_categories=("financial_literacy", "banking_basics", "responsible_borrowing", "consumer_protection", "digital_financial_safety", "complaint_guidance", "cooperative_banking"),
        discovery_path_prefixes=("/documents/", "/scripts/", "/commonman/", "/commonperson/", "/notification"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="cpgrams",
        name="CPGRAMS",
        category="public_grievances",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pgportal.gov.in",),
        crawl_targets=(
            CrawlTarget("https://pgportal.gov.in/", ("grievance_lodging", "grievance_tracking", "appeals")),
            CrawlTarget("https://www.pgportal.gov.in/Home/Faq", ("grievance_procedure", "deadlines", "appeals")),
            CrawlTarget("https://www.pgportal.gov.in/Home/OtherGuidlines", ("grievance_guidelines",)),
            CrawlTarget("https://pgportal.gov.in/Home/Preview/Q29tcHJlaGVuc2l2ZUd1aWRlbGluZXNGb3JIYW5kbGluZ1RoZVB1YmxpY0dyaWV2YW5jZXMucGRm", ("grievance_procedure", "grievance_guidelines", "appeals")),
        ),
        expected_categories=("grievance_lodging", "grievance_tracking", "grievance_procedure", "grievance_guidelines", "appeals", "deadlines"),
        discovery_path_prefixes=("/Home/Preview/", "/Home/Faq", "/Home/OtherGuidlines", "/docs/", "/files/"),
        max_documents_per_check=50,
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
