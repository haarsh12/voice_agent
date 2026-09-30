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
    ApprovedSourceDefinition(
        key="ncdc",
        name="National Cooperative Development Corporation (NCDC)",
        category="cooperative_financing",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("ncdc.in",),
        crawl_targets=(
            CrawlTarget("https://www.ncdc.in/", ("ncdc_schemes", "cooperative_financing", "yuva_sahakar", "sahakar_mitra")),
            CrawlTarget("https://www.ncdc.in/schemes", ("ncdc_schemes", "cooperative_financing", "dairy_sahakar", "ayushman_sahakar")),
            CrawlTarget("https://www.ncdc.in/yuva-sahakar", ("yuva_sahakar", "youth_cooperative", "startup_support")),
            CrawlTarget("https://www.ncdc.in/sahakar-mitra", ("sahakar_mitra", "internship", "cooperative_professionals")),
            CrawlTarget("https://www.ncdc.in/dairy-schemes", ("dairy_sahakar", "dairy_cooperative", "milk_processing")),
            CrawlTarget("https://www.ncdc.in/guidelines", ("ncdc_guidelines", "application_process", "eligibility")),
        ),
        expected_categories=("ncdc_schemes", "cooperative_financing", "yuva_sahakar", "sahakar_mitra", "dairy_sahakar", "ayushman_sahakar", "nandini_sahakar", "digital_sahakar", "integrated_cooperative_development", "share_capital_assistance", "margin_money_assistance"),
        discovery_path_prefixes=("/schemes/", "/guidelines/", "/circulars/", "/notifications/", "/documents/", "/downloads/", "/pdf/"),
        max_documents_per_check=80,
    ),
    ApprovedSourceDefinition(
        key="pm_kisan",
        name="PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        category="farmer_income_support",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pmkisan.gov.in",),
        crawl_targets=(
            CrawlTarget("https://pmkisan.gov.in/", ("pm_kisan_scheme", "farmer_income_support", "direct_benefit_transfer")),
            CrawlTarget("https://pmkisan.gov.in/Documents.aspx", ("guidelines", "operational_guidelines", "eligibility")),
            CrawlTarget("https://pmkisan.gov.in/FarmerStatus.aspx", ("application_status", "beneficiary_status", "payment_tracking")),
        ),
        expected_categories=("pm_kisan_scheme", "farmer_income_support", "direct_benefit_transfer", "eligibility", "beneficiary_list", "payment_tracking"),
        discovery_path_prefixes=("/Documents/", "/Notifications/", "/Guidelines/", "/pdf/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="kisan_credit_card",
        name="Kisan Credit Card (KCC)",
        category="agricultural_credit",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pmkisan.gov.in", "nabard.org", "agriwelfare.gov.in"),
        crawl_targets=(
            CrawlTarget("https://pmkisan.gov.in/Rpt_KCC.aspx", ("kisan_credit_card", "agricultural_credit", "eligibility")),
            CrawlTarget("https://www.nabard.org/content1.aspx?catid=497", ("kcc_guidelines", "credit_limits", "interest_subvention")),
        ),
        expected_categories=("kisan_credit_card", "agricultural_credit", "interest_subvention", "crop_loan", "eligibility", "application_process"),
        discovery_path_prefixes=("/content/", "/documents/", "/pdf/", "/Guidelines/"),
        max_documents_per_check=40,
    ),
    ApprovedSourceDefinition(
        key="agriculture_infrastructure_fund",
        name="Agriculture Infrastructure Fund (AIF)",
        category="agricultural_infrastructure",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("agriinfra.dac.gov.in",),
        crawl_targets=(
            CrawlTarget("https://agriinfra.dac.gov.in/", ("agriculture_infrastructure_fund", "financing_facility", "project_financing")),
            CrawlTarget("https://agriinfra.dac.gov.in/Schemes.aspx", ("scheme_guidelines", "eligible_activities", "interest_subvention")),
            CrawlTarget("https://agriinfra.dac.gov.in/FAQ.aspx", ("faqs", "application_process", "eligibility")),
        ),
        expected_categories=("agriculture_infrastructure_fund", "financing_facility", "post_harvest_management", "community_farming_assets", "interest_subvention", "credit_guarantee"),
        discovery_path_prefixes=("/documents/", "/guidelines/", "/pdf/", "/schemes/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="pmksy",
        name="Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
        category="irrigation",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pmksy.gov.in",),
        crawl_targets=(
            CrawlTarget("https://pmksy.gov.in/", ("pmksy_scheme", "micro_irrigation", "watershed_development")),
            CrawlTarget("https://pmksy.gov.in/Guidelines.aspx", ("scheme_guidelines", "per_drop_more_crop", "accelerated_irrigation")),
            CrawlTarget("https://pmksy.gov.in/AboutPMKSY.aspx", ("scheme_components", "objectives", "implementation")),
        ),
        expected_categories=("pmksy_scheme", "micro_irrigation", "per_drop_more_crop", "watershed_development", "accelerated_irrigation", "irrigation_support"),
        discovery_path_prefixes=("/documents/", "/guidelines/", "/schemes/", "/pdf/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="ministry_of_fisheries",
        name="Department of Fisheries",
        category="fisheries_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("dof.gov.in",),
        crawl_targets=(
            CrawlTarget("https://dof.gov.in/", ("fisheries_policy", "pmmsy", "fisheries_schemes")),
            CrawlTarget("https://dof.gov.in/pmmsy", ("pmmsy_scheme", "fisheries_infrastructure", "value_chain")),
            CrawlTarget("https://dof.gov.in/schemes", ("fisheries_schemes", "blue_revolution", "fisheries_development")),
            CrawlTarget("https://dof.gov.in/fidf", ("fisheries_infrastructure_fund", "fidf_scheme", "financing")),
        ),
        expected_categories=("pmmsy_scheme", "fisheries_infrastructure", "blue_revolution", "fidf_scheme", "fisheries_cooperative", "aquaculture", "inland_fisheries", "marine_fisheries"),
        discovery_path_prefixes=("/schemes/", "/guidelines/", "/documents/", "/pdf/", "/notifications/"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="department_animal_husbandry_dairying",
        name="Department of Animal Husbandry & Dairying",
        category="livestock_dairy_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("dahd.nic.in",),
        crawl_targets=(
            CrawlTarget("https://dahd.nic.in/", ("livestock_policy", "dairy_development", "animal_husbandry")),
            CrawlTarget("https://dahd.nic.in/schemes/programmes", ("rashtriya_gokul_mission", "national_livestock_mission", "dairy_schemes")),
            CrawlTarget("https://dahd.nic.in/related-links/rashtriya-gokul-mission", ("rashtriya_gokul_mission", "breed_improvement", "indigenous_breeds")),
            CrawlTarget("https://dahd.nic.in/related-links/national-programme-for-dairy-development", ("dairy_development", "dairy_cooperative", "milk_production")),
        ),
        expected_categories=("rashtriya_gokul_mission", "national_livestock_mission", "dairy_development", "livestock_health", "breed_improvement", "fodder_development", "dairy_cooperative", "poultry_development"),
        discovery_path_prefixes=("/schemes/", "/documents/", "/related-links/", "/pdf/", "/guidelines/"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="food_processing_ministry",
        name="Ministry of Food Processing Industries",
        category="food_processing_policy",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("mofpi.gov.in",),
        crawl_targets=(
            CrawlTarget("https://www.mofpi.gov.in/", ("food_processing_policy", "pmfme", "sampada_yojana")),
            CrawlTarget("https://www.mofpi.gov.in/pmfme", ("pmfme_scheme", "micro_food_enterprises", "fpo_support")),
            CrawlTarget("https://www.mofpi.gov.in/Schemes/pradhan-mantri-kisan-sampada-yojana", ("sampada_yojana", "food_processing_infrastructure", "value_chain")),
        ),
        expected_categories=("pmfme_scheme", "sampada_yojana", "food_processing_infrastructure", "cold_chain", "mega_food_parks", "value_addition", "backward_forward_linkages"),
        discovery_path_prefixes=("/Schemes/", "/Documents/", "/schemes/", "/guidelines/", "/pdf/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="trifed",
        name="TRIFED (Tribal Cooperative Marketing Development Federation)",
        category="tribal_welfare",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("trifed.tribal.gov.in", "trifed.in"),
        crawl_targets=(
            CrawlTarget("https://trifed.tribal.gov.in/", ("tribal_marketing", "van_dhan_vikas", "minor_forest_produce")),
            CrawlTarget("https://trifed.tribal.gov.in/vandhan", ("van_dhan_vikas_kendra", "tribal_entrepreneurship", "mfp_value_chain")),
            CrawlTarget("https://trifed.tribal.gov.in/schemes", ("tribal_schemes", "msp_for_mfp", "tribal_cooperative")),
        ),
        expected_categories=("van_dhan_vikas_kendra", "tribal_marketing", "minor_forest_produce", "msp_for_mfp", "tribal_cooperative", "tribal_entrepreneurship", "tribal_livelihood"),
        discovery_path_prefixes=("/schemes/", "/vandhan/", "/documents/", "/pdf/", "/guidelines/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="fpo_formation",
        name="FPO Formation & Promotion Scheme",
        category="farmer_producer_organisations",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("sfacindia.com", "nabard.org", "agriwelfare.gov.in"),
        crawl_targets=(
            CrawlTarget("https://www.sfacindia.com/", ("fpo_formation", "fpo_promotion", "equity_grant")),
            CrawlTarget("https://www.nabard.org/content1.aspx?id=602", ("fpo_guidelines", "producer_organisations", "nafpo")),
        ),
        expected_categories=("fpo_formation", "fpo_promotion", "equity_grant", "credit_guarantee", "management_support", "marketing_support", "nafpo"),
        discovery_path_prefixes=("/schemes/", "/documents/", "/content/", "/guidelines/", "/pdf/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="maharashtra_agriculture",
        name="Maharashtra Agriculture Department",
        category="state_agriculture",
        authority_level=95,
        geographic_scope="STATE",
        check_interval_hours=24,
        approved_domains=("krishi.maharashtra.gov.in",),
        crawl_targets=(
            CrawlTarget("https://krishi.maharashtra.gov.in/", ("maharashtra_agriculture_schemes", "state_farmer_programs", "subsidies")),
            CrawlTarget("https://krishi.maharashtra.gov.in/Site/Public/Schemes.aspx", ("state_schemes", "agricultural_subsidies", "farmer_support")),
        ),
        expected_categories=("maharashtra_agriculture_schemes", "chhatrapati_shivaji_shetkari_sanman", "mahatma_jyotiba_phule_karjamukti", "agricultural_subsidies", "state_farmer_support", "cotton_procurement"),
        discovery_path_prefixes=("/Site/", "/documents/", "/schemes/", "/pdf/", "/Public/"),
        max_documents_per_check=60,
    ),
    ApprovedSourceDefinition(
        key="soil_health_card",
        name="Soil Health Card Scheme",
        category="soil_health",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("soilhealth.dac.gov.in",),
        crawl_targets=(
            CrawlTarget("https://soilhealth.dac.gov.in/", ("soil_health_card", "soil_testing", "nutrient_management")),
            CrawlTarget("https://soilhealth.dac.gov.in/about", ("scheme_guidelines", "soil_testing_labs", "farmer_benefits")),
        ),
        expected_categories=("soil_health_card", "soil_testing", "nutrient_management", "fertilizer_recommendation", "soil_health_management"),
        discovery_path_prefixes=("/documents/", "/guidelines/", "/about/", "/pdf/"),
        max_documents_per_check=40,
    ),
    ApprovedSourceDefinition(
        key="paramparagat_krishi_vikas",
        name="Paramparagat Krishi Vikas Yojana (PKVY)",
        category="organic_farming",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("pgsindia-ncof.gov.in", "agriwelfare.gov.in"),
        crawl_targets=(
            CrawlTarget("https://pgsindia-ncof.gov.in/PKVY/Index.aspx", ("pkvy_scheme", "organic_farming", "cluster_formation")),
            CrawlTarget("https://pgsindia-ncof.gov.in/PKVY/AboutPKVY.aspx", ("scheme_guidelines", "organic_certification", "financial_assistance")),
        ),
        expected_categories=("pkvy_scheme", "organic_farming", "organic_certification", "cluster_formation", "financial_assistance", "sustainable_agriculture"),
        discovery_path_prefixes=("/PKVY/", "/documents/", "/guidelines/", "/pdf/"),
        max_documents_per_check=40,
    ),
    ApprovedSourceDefinition(
        key="sub_mission_agricultural_mechanization",
        name="Sub-Mission on Agricultural Mechanization (SMAM)",
        category="agricultural_mechanization",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("agrimachinery.nic.in", "agriwelfare.gov.in"),
        crawl_targets=(
            CrawlTarget("https://agrimachinery.nic.in/", ("smam_scheme", "agricultural_mechanization", "chc_scheme")),
            CrawlTarget("https://agrimachinery.nic.in/Guidelines.aspx", ("scheme_guidelines", "subsidy_rates", "eligible_machinery")),
        ),
        expected_categories=("smam_scheme", "agricultural_mechanization", "custom_hiring_centers", "farm_machinery_subsidy", "machinery_training"),
        discovery_path_prefixes=("/Guidelines/", "/documents/", "/pdf/", "/schemes/"),
        max_documents_per_check=40,
    ),
    ApprovedSourceDefinition(
        key="horticulture_mission",
        name="Mission for Integrated Development of Horticulture (MIDH)",
        category="horticulture",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("midh.gov.in",),
        crawl_targets=(
            CrawlTarget("https://midh.gov.in/", ("midh_scheme", "horticulture_development", "area_expansion")),
            CrawlTarget("https://midh.gov.in/aboutmidh.aspx", ("scheme_components", "operational_guidelines", "assistance_rates")),
        ),
        expected_categories=("midh_scheme", "horticulture_development", "area_expansion", "planting_material", "protected_cultivation", "post_harvest_management", "marketing_infrastructure"),
        discovery_path_prefixes=("/documents/", "/guidelines/", "/pdf/", "/aboutmidh/"),
        max_documents_per_check=50,
    ),
    ApprovedSourceDefinition(
        key="e_nam",
        name="e-NAM (National Agriculture Market)",
        category="agricultural_marketing",
        authority_level=95,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("enam.gov.in",),
        crawl_targets=(
            CrawlTarget("https://enam.gov.in/web/", ("e_nam_platform", "agricultural_marketing", "price_discovery")),
            CrawlTarget("https://enam.gov.in/web/resources/faq", ("faqs", "registration", "trading_process")),
        ),
        expected_categories=("e_nam_platform", "agricultural_marketing", "price_discovery", "mandi_integration", "farmer_registration", "trader_registration"),
        discovery_path_prefixes=("/web/", "/resources/", "/documents/", "/pdf/"),
        max_documents_per_check=40,
    ),
    ApprovedSourceDefinition(
        key="minimum_support_price",
        name="Minimum Support Price (MSP) Operations",
        category="procurement",
        authority_level=100,
        geographic_scope="NATIONAL",
        check_interval_hours=24,
        approved_domains=("cacp.dacnet.nic.in", "fci.gov.in"),
        crawl_targets=(
            CrawlTarget("https://cacp.dacnet.nic.in/", ("minimum_support_price", "procurement_policy", "msp_rates")),
            CrawlTarget("https://fci.gov.in/procurements.php", ("procurement_operations", "msp_implementation", "grain_procurement")),
        ),
        expected_categories=("minimum_support_price", "procurement_policy", "msp_rates", "procurement_operations", "grain_procurement", "price_support"),
        discovery_path_prefixes=("/ViewQuestionare/", "/documents/", "/pdf/", "/procurements/"),
        max_documents_per_check=40,
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
