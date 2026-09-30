export type HealthResponse = {
  status: 'ok'
  agent_name: string
  configured: boolean
  default_language: SupportedLanguage
}

export type TextChatResponse = {
  message: string
  language: SupportedLanguage
  document_name: string | null
  document_truncated: boolean
  evidence_status: EvidenceStatus
  sources: OfficialSourceReference[]
}

export type SchemeSummary = {
  id: string
  slug: string
  official_name: string
  short_name: string | null
  scheme_type: string
  category: string
  description: string | null
  beneficiary_categories: string[]
  relevant_user_types: string[]
  applicable_states: string[]
  applicable_districts: string[]
  geographic_scope: string
  status: 'ACTIVE' | 'UPCOMING' | 'APPLICATION_OPEN' | 'APPLICATION_CLOSED' | 'PAUSED' | 'SUPERSEDED' | 'DISCONTINUED' | 'EXPIRED' | 'UNKNOWN'
  verification_status: 'APPROVED' | 'REVIEW_REQUIRED'
  last_checked_at: string
}

export type SchemeSource = {
  source_name: string
  title: string
  url: string
  relevant_section: string | null
  page_number: number | null
  document_version: number | null
}

export type SchemeDetail = SchemeSummary & {
  data: Record<string, unknown>
  sources: SchemeSource[]
  current_version_number: number | null
}

export type SchemeSearchResponse = {
  items: SchemeSummary[]
  total: number
  offset: number
  limit: number
}

export type SchemeFilters = {
  categories: string[]
  beneficiaries: string[]
  states: string[]
  types: string[]
}

export const GRIEVANCE_STATUSES = [
  'DRAFT', 'READY_FOR_CONFIRMATION', 'USER_CONFIRMED', 'SUBMITTING',
  'SUBMITTED', 'ACKNOWLEDGED', 'UNDER_PROCESS', 'ACTION_REQUIRED',
  'RESOLVED', 'CLOSED', 'ESCALATED', 'APPEAL_AVAILABLE',
  'APPEAL_SUBMITTED', 'SUBMISSION_FAILED', 'UNKNOWN',
] as const

export type GrievanceStatus = (typeof GRIEVANCE_STATUSES)[number]

export const GRIEVANCE_CATEGORIES = [
  'PACS_ISSUE', 'COOPERATIVE_SOCIETY', 'PAYMENT', 'LOAN', 'INSURANCE_CLAIM',
  'GOVERNMENT_SCHEME', 'AGRICULTURE_SERVICE', 'FINANCIAL_SERVICE',
  'DOCUMENT_CERTIFICATE', 'ADMINISTRATIVE', 'OTHER_GOVERNMENT',
] as const

export type GrievanceCategory = (typeof GRIEVANCE_CATEGORIES)[number]

export type GrievanceEvent = {
  event_type: string
  from_status: GrievanceStatus | null
  to_status: GrievanceStatus | null
  actor: 'MEMBER' | 'SYSTEM' | 'ADMIN' | 'OFFICIAL_SYNC'
  created_at: string
  message: string
}

export type Grievance = {
  id: string
  status: GrievanceStatus
  category: GrievanceCategory
  subject: string | null
  description: string | null
  original_language: string | null
  organization: string | null
  state: string | null
  district: string | null
  locality: string | null
  incident_date: string | null
  amount_description: string | null
  has_contacted_organization: boolean | null
  prior_reference: string | null
  authority_name: string | null
  destination_name: string | null
  destination_url: string | null
  official_tracking_url: string | null
  routing_reason: string | null
  submission_method: 'PORTAL_HANDOFF' | null
  official_reference: string | null
  official_reference_source: 'MEMBER_REPORTED' | null
  created_at: string
  updated_at: string
  confirmed_at: string | null
  handoff_opened_at: string | null
  submitted_at: string | null
  acknowledged_at: string | null
  last_status_checked_at: string | null
  status_changed_at: string
  version: number
  missing_fields: string[]
  events: GrievanceEvent[]
}

export type GrievanceListResponse = {
  items: Grievance[]
  total: number
  offset: number
  limit: number
}

export type GrievanceDraftInput = {
  category?: GrievanceCategory
  subject?: string | null
  description?: string | null
  original_language?: string | null
  organization?: string | null
  state?: string | null
  district?: string | null
  locality?: string | null
  incident_date?: string | null
  amount_description?: string | null
  has_contacted_organization?: boolean | null
  prior_reference?: string | null
}

export type EvidenceStatus =
  | 'VERIFIED_SOURCE'
  | 'MULTIPLE_VERIFIED_SOURCES'
  | 'PARTIALLY_VERIFIED'
  | 'GENERAL_MODEL_KNOWLEDGE'
  | 'GENERAL_GUIDANCE'
  | 'INSUFFICIENT_EVIDENCE'

export type OfficialSourceReference = {
  name: string
  title: string
  url: string
  document_version: string | null
  freshness_status: 'CURRENT' | 'SUPERSEDED' | 'EXPIRED' | 'REVIEW_REQUIRED' | 'UNKNOWN' | 'FETCH_FAILED' | 'EXTRACTION_FAILED'
}

export type GuestSession = {
  session_id: string
  session_secret: string
}

export type AdminSession = {
  authenticated: boolean
}

export type KnowledgeBaseCheck = {
  started_at: string
  completed_at: string | null
  result: 'UNCHANGED' | 'CHANGED' | 'PARTIAL_FAILURE' | 'FAILED'
  checked_documents: number
  changed_documents: number
}

export type KnowledgeBaseSource = {
  key: string
  name: string
  category: string
  geographic_scope: string
  approved_domains: string[]
  entry_urls: string[]
  expected_categories: string[]
  covered_categories: string[]
  missing_categories: string[]
  coverage_state: 'COMPLETE' | 'PARTIAL' | 'INCOMPLETE' | 'UNKNOWN'
  ingestion_state: 'INGESTED' | 'NOT_INGESTED'
  failed_resource_count: number
  validation_status: 'APPROVED' | 'DISABLED' | 'CHECK_FAILED' | 'REVIEW_REQUIRED'
  check_interval_hours: number
  last_successful_check_at: string | null
  last_detected_change_at: string | null
  last_successful_ingestion_at: string | null
  current_document_count: number
  chunk_count: number
  latest_check: KnowledgeBaseCheck | null
}

export type KnowledgeBaseDocument = {
  source_key: string
  source_name: string
  title: string
  url: string
  version_number: number
  status: 'CURRENT' | 'SUPERSEDED' | 'EXPIRED' | 'REVIEW_REQUIRED' | 'UNKNOWN' | 'FETCH_FAILED' | 'EXTRACTION_FAILED'
  last_checked_at: string
  first_retrieved_at: string
  extraction_method: string | null
  is_ocr: boolean
}

export type KnowledgeBaseStatus = {
  generated_at: string
  storage: {
    vector_index: 'connected' | 'not_configured' | 'unavailable'
    vector_point_count: number | null
    source_count: number
    document_count: number
    current_document_count: number
    chunk_count: number
  }
  sources: KnowledgeBaseSource[]
  recent_documents: KnowledgeBaseDocument[]
}

export const USER_TYPES = [
  'cooperative_member',
  'farmer',
  'pacs_member',
  'cooperative_official',
  'rural_stakeholder',
  'other',
] as const

export type UserType = (typeof USER_TYPES)[number]

export type SahayakProfile = {
  full_name: string | null
  phone_number: string
  state: string | null
  district: string | null
  village_or_town: string | null
  address: string | null
  user_type: UserType | null
  cooperative_role: string | null
  needs_onboarding: boolean
  face_id_enabled: boolean
}

export type VerifiedProfile = SahayakProfile & {
  is_new_user: boolean
}

export type ProfileUpdate = {
  full_name?: string
  state?: string
  district?: string
  village_or_town?: string
  address?: string
  user_type?: UserType
  cooperative_role?: string
}

export const SUPPORTED_LANGUAGE_CODES = [
  'hi-IN',
  'mr-IN',
  'en-IN',
  'ta-IN',
  'te-IN',
  'kn-IN',
  'ml-IN',
  'gu-IN',
  'bn-IN',
  'pa-IN',
] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGE_CODES)[number]

export function isSupportedLanguage(value: unknown): value is SupportedLanguage {
  return (
    typeof value === 'string' &&
    (SUPPORTED_LANGUAGE_CODES as readonly string[]).includes(value)
  )
}
