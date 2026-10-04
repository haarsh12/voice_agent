import type {
  AdminSession,
  CasteCategory,
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
  Grievance,
  GrievanceDraftInput,
  GrievanceListResponse,
  GrievanceStatus,
} from '../types/api'
import type { ServerWebAuthnOptions, WebAuthnCredentialJSON } from './webauthn'
import { cache } from './cache'

// Local Vite development uses the same-origin /api proxy. This works when the
// site is opened from another device on the LAN; 127.0.0.1 would otherwise
// point to that device rather than the computer running FastAPI. Deployments
// set VITE_API_BASE_URL to their public API origin.
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const apiBaseUrl = configuredApiBaseUrl ? configuredApiBaseUrl.replace(/\/$/, '') : ''

export const agentName = import.meta.env.VITE_AGENT_NAME ?? 'sahayak-ai'
// In kiosk builds (.env.kiosk) this is 'raspberrypi'; website builds use 'website'
const clientDevice = (import.meta.env.VITE_CLIENT_DEVICE as string | undefined) ?? 'website'

function clientDeviceHeaders(): HeadersInit {
  return { 'X-Sahayak-Device': clientDevice }
}

export function getTokenEndpoint(): string {
  // LiveKit TokenSource owns the request headers. Declare the same device in
  // its endpoint query while every ordinary API request uses the standard
  // X-Sahayak-Device header below.
  return `${apiBaseUrl}/api/token?client_device=${encodeURIComponent(clientDevice)}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers, ...requestInit } = init ?? {}
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...requestInit,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...clientDeviceHeaders(), ...headers },
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
  useCache?: boolean
} = {}): Promise<SchemeSearchResponse> {
  const query = new URLSearchParams()
  if (params.query?.trim()) query.set('query', params.query.trim())
  if (params.category) query.set('category', params.category)
  if (params.beneficiary) query.set('beneficiary', params.beneficiary)
  if (params.state?.trim()) query.set('state', params.state.trim())
  if (params.relevantToMe) query.set('relevant_to_me', 'true')
  if (params.offset) query.set('offset', String(params.offset))
  const suffix = query.size ? `?${query.toString()}` : ''
  const endpoint = `/api/schemes${suffix}`
  
  // Use cache if requested and offset is 0 (first page)
  if (params.useCache !== false && (params.offset ?? 0) === 0) {
    const cacheKey = `schemes_${suffix}`
    const cached = cache.get<SchemeSearchResponse>(cacheKey)
    if (cached) return Promise.resolve(cached)
    
    return request<SchemeSearchResponse>(endpoint).then((result) => {
      cache.set(cacheKey, result, { ttl: 3 * 60 * 1000 }) // 3 minutes
      return result
    })
  }
  
  return request<SchemeSearchResponse>(endpoint)
}

export function getSchemeFilters(): Promise<SchemeFilters> {
  const cacheKey = 'scheme_filters'
  const cached = cache.get<SchemeFilters>(cacheKey)
  if (cached) return Promise.resolve(cached)
  
  return request<SchemeFilters>('/api/schemes/filters').then((result) => {
    cache.set(cacheKey, result, { ttl: 10 * 60 * 1000 }) // 10 minutes
    return result
  })
}

export function getSchemeDetail(identifier: string): Promise<SchemeDetail> {
  const cacheKey = `scheme_detail_${identifier}`
  const cached = cache.get<SchemeDetail>(cacheKey)
  if (cached) return Promise.resolve(cached)
  
  return request<SchemeDetail>(`/api/schemes/${encodeURIComponent(identifier)}`).then((result) => {
    cache.set(cacheKey, result, { ttl: 5 * 60 * 1000 }) // 5 minutes
    return result
  })
}

export function getGrievances(params: { state?: GrievanceStatus; query?: string } = {}): Promise<GrievanceListResponse> {
  const query = new URLSearchParams()
  if (params.state) query.set('state', params.state)
  if (params.query?.trim()) query.set('query', params.query.trim())
  const suffix = query.size ? `?${query.toString()}` : ''
  return request<GrievanceListResponse>(`/api/grievances${suffix}`)
}

export function getGrievance(id: string): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}`)
}

export function createGrievance(payload: GrievanceDraftInput): Promise<Grievance> {
  return request<Grievance>('/api/grievances', {
    method: 'POST', headers: csrfHeaders(), body: JSON.stringify(payload),
  })
}

export function updateGrievance(id: string, version: number, payload: GrievanceDraftInput): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}`, {
    method: 'PUT', headers: csrfHeaders(), body: JSON.stringify({ ...payload, version }),
  })
}

export function readyGrievance(id: string, version: number): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}/ready`, {
    method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ version }),
  })
}

export function confirmGrievance(id: string, version: number): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}/confirm`, {
    method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ version, confirmed: true }),
  })
}

export function recordOfficialHandoff(id: string, version: number): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}/official-handoff`, {
    method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ version }),
  })
}

export function recordOfficialReference(id: string, version: number, officialReference: string): Promise<Grievance> {
  return request<Grievance>(`/api/grievances/${encodeURIComponent(id)}/official-reference`, {
    method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ version, official_reference: officialReference }),
  })
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

export function getKnowledgeBaseStatus(useCache = true): Promise<KnowledgeBaseStatus> {
  const cacheKey = 'knowledge_base_status'
  
  if (useCache) {
    const cached = cache.get<KnowledgeBaseStatus>(cacheKey)
    if (cached) return Promise.resolve(cached)
  }
  
  return request<KnowledgeBaseStatus>('/api/knowledge/status').then((result) => {
    cache.set(cacheKey, result, { ttl: 2 * 60 * 1000 }) // 2 minutes for knowledge base
    return result
  })
}

export async function endAdminSession(): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/admin/session`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { ...clientDeviceHeaders(), ...adminCsrfHeaders() },
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
    headers: { ...clientDeviceHeaders(), 'X-Sahayak-Guest-Secret': session.session_secret },
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
    headers: clientDeviceHeaders(),
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
  address: string
  pincode: string
  caste_category: CasteCategory
  user_type: UserType
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
    headers: { ...clientDeviceHeaders(), ...csrfHeaders() },
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
    headers: { ...clientDeviceHeaders(), ...csrfHeaders() },
  })
  if (!response.ok && response.status !== 401) throw new Error(await getSafeError(response))
}
