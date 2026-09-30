import type {
  AdminSession,
  GuestSession,
  HealthResponse,
  KnowledgeBaseStatus,
  ProfileUpdate,
  SahayakProfile,
  SupportedLanguage,
  TextChatResponse,
  VerifiedProfile,
  UserType,
  SchemeDetail,
  SchemeFilters,
  SchemeSearchResponse,
} from '../types/api'
import type { ServerWebAuthnOptions, WebAuthnCredentialJSON } from './webauthn'

// Local Vite development uses the same-origin /api proxy. This works when the
// site is opened from another device on the LAN; 127.0.0.1 would otherwise
// point to that device rather than the computer running FastAPI. Deployments
// set VITE_API_BASE_URL to their public API origin.
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const apiBaseUrl = configuredApiBaseUrl ? configuredApiBaseUrl.replace(/\/$/, '') : ''

export const agentName = import.meta.env.VITE_AGENT_NAME ?? 'sahayak-ai'

export function getTokenEndpoint(): string {
  return `${apiBaseUrl}/api/token`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers, ...requestInit } = init ?? {}
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...requestInit,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...headers },
    })
  } catch {
    throw new Error('Sahayak AI cannot reach its local service. Refresh this page, then make sure the API is running.')
  }

  if (!response.ok) {
    throw new Error(await getSafeError(response))
  }

  return (await response.json()) as T
}

async function getSafeError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // A reverse proxy may return a non-JSON error page. Keep it out of the UI.
  }
  if (response.status === 401) return 'Your session has expired. Please sign in again.'
  if (response.status === 429) return 'Too many attempts. Please wait a moment and try again.'
  if (response.status === 502 || response.status === 503) return 'Sahayak AI is starting. Please wait a moment and try again.'
  return 'We could not complete that request. Please try again.'
}

function csrfHeaders(): HeadersInit {
  const csrfToken = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith('sahayak_csrf='))
    ?.split('=')[1]
  return csrfToken ? { 'X-Sahayak-CSRF': decodeURIComponent(csrfToken) } : {}
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export function getSchemes(params: {
  query?: string
  category?: string
  beneficiary?: string
  state?: string
  relevantToMe?: boolean
  offset?: number
} = {}): Promise<SchemeSearchResponse> {
  const query = new URLSearchParams()
  if (params.query?.trim()) query.set('query', params.query.trim())
  if (params.category) query.set('category', params.category)
  if (params.beneficiary) query.set('beneficiary', params.beneficiary)
  if (params.state?.trim()) query.set('state', params.state.trim())
  if (params.relevantToMe) query.set('relevant_to_me', 'true')
  if (params.offset) query.set('offset', String(params.offset))
  const suffix = query.size ? `?${query.toString()}` : ''
  return request<SchemeSearchResponse>(`/api/schemes${suffix}`)
}

export function getSchemeFilters(): Promise<SchemeFilters> {
  return request<SchemeFilters>('/api/schemes/filters')
}

export function getSchemeDetail(identifier: string): Promise<SchemeDetail> {
  return request<SchemeDetail>(`/api/schemes/${encodeURIComponent(identifier)}`)
}

function adminCsrfHeaders(): HeadersInit {
  const csrfToken = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith('sahayak_admin_csrf='))
    ?.split('=')[1]
  return csrfToken ? { 'X-Sahayak-Admin-CSRF': decodeURIComponent(csrfToken) } : {}
}

export function startAdminSession(adminId: string, password: string): Promise<AdminSession> {
  return request('/api/admin/session', {
    method: 'POST',
    body: JSON.stringify({ admin_id: adminId, password }),
  })
}

export function getAdminSession(): Promise<AdminSession> {
  return request('/api/admin/session')
}

export function getKnowledgeBaseStatus(): Promise<KnowledgeBaseStatus> {
  return request('/api/knowledge-base/status')
}

export async function endAdminSession(): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/admin/session`, {
    method: 'DELETE',
    credentials: 'include',
    headers: adminCsrfHeaders(),
  })
  if (!response.ok) throw new Error(await getSafeError(response))
}

export function createGuestSession(): Promise<GuestSession> {
  return request<GuestSession>('/api/guest-sessions', { method: 'POST' })
}

export async function deleteGuestSession(session: GuestSession): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/guest-sessions/${encodeURIComponent(session.session_id)}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'X-Sahayak-Guest-Secret': session.session_secret },
  })
  // The session may already have expired. In either case it has no remaining
  // usable context, so the browser can safely create a fresh session.
  if (!response.ok && response.status !== 410) {
    throw new Error('The previous guest session could not be cleared.')
  }
}

export async function sendTextChat(
  message: string,
  language: SupportedLanguage,
  document: File | null,
  guestSession: GuestSession,
): Promise<TextChatResponse> {
  const form = new FormData()
  form.set('message', message)
  form.set('language', language)
  form.set('guest_session_id', guestSession.session_id)
  form.set('guest_session_secret', guestSession.session_secret)
  if (document) form.set('document', document)

  const response = await fetch(`${apiBaseUrl}/api/chat`, {
    method: 'POST',
    credentials: 'include',
    body: form,
  })

  if (!response.ok) {
    let detail = 'The text chat request could not be completed.'
    try {
      const body: unknown = await response.json()
      if (
        body &&
        typeof body === 'object' &&
        'detail' in body &&
        typeof body.detail === 'string'
      ) {
        detail = body.detail
      }
    } catch {
      // Preserve a safe generic error when a proxy returns non-JSON content.
    }
    throw new Error(detail)
  }

  return (await response.json()) as TextChatResponse
}

export type MobileAuthIntent = 'login' | 'register'

export type RegistrationPayload = {
  full_name: string
  state: string
  district: string
  village_or_town: string
  user_type: UserType
  address?: string
  cooperative_role?: string
}

export function requestOtp(phoneNumber: string, intent: MobileAuthIntent): Promise<{ message: string }> {
  return request('/api/auth/otp/request', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, intent }),
  })
}

export function verifyOtp(
  phoneNumber: string,
  otpCode: string,
  intent: MobileAuthIntent,
  registration?: RegistrationPayload,
): Promise<VerifiedProfile> {
  return request('/api/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({
      phone_number: phoneNumber,
      otp_code: otpCode,
      intent,
      ...(registration ? { registration } : {}),
    }),
  })
}

export function getProfile(): Promise<SahayakProfile> {
  return request('/api/auth/profile')
}

type WebAuthnOptionsResponse = {
  ceremony_id: string
  public_key: ServerWebAuthnOptions
}

export function startFaceIdRegistration(): Promise<WebAuthnOptionsResponse> {
  return request('/api/auth/face-id/registration/options', { method: 'POST', headers: csrfHeaders() })
}

export function finishFaceIdRegistration(
  ceremonyId: string,
  credential: WebAuthnCredentialJSON,
): Promise<SahayakProfile> {
  return request('/api/auth/face-id/registration/verify', {
    method: 'POST',
    headers: csrfHeaders(),
    body: JSON.stringify({ ceremony_id: ceremonyId, credential }),
  })
}

export function startFaceIdAuthentication(): Promise<WebAuthnOptionsResponse> {
  return request('/api/auth/face-id/authentication/options', { method: 'POST' })
}

export function finishFaceIdAuthentication(
  ceremonyId: string,
  credential: WebAuthnCredentialJSON,
): Promise<SahayakProfile> {
  return request('/api/auth/face-id/authentication/verify', {
    method: 'POST',
    body: JSON.stringify({ ceremony_id: ceremonyId, credential }),
  })
}

export function removeFaceId(): Promise<SahayakProfile> {
  return request('/api/auth/face-id', { method: 'DELETE', headers: csrfHeaders() })
}

export function updateProfile(payload: ProfileUpdate): Promise<SahayakProfile> {
  return request('/api/auth/profile', {
    method: 'PUT',
    headers: csrfHeaders(),
    body: JSON.stringify(payload),
  })
}

export async function signOut(): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/auth/logout`, {
    method: 'POST',
    credentials: 'include',
    headers: csrfHeaders(),
  })
  if (!response.ok && response.status !== 401) throw new Error(await getSafeError(response))
}
