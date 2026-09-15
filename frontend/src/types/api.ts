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
  sources: OfficialSourceReference[]
}

export type OfficialSourceReference = {
  name: string
  url: string
}

export type GuestSession = {
  session_id: string
  session_secret: string
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
