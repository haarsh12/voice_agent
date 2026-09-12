export type HealthResponse = {
  status: 'ok'
  agent_name: string
  configured: boolean
  default_language: SupportedLanguage
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
