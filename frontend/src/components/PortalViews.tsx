import { type ChangeEvent, type FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import {
  Bell,
  BookOpenCheck,
  ChevronRight,
  FilePlus2,
  FileText,
  Fingerprint,
  Landmark,
  LoaderCircle,
  MessageSquareWarning,
  Mic,
  MoreHorizontal,
  Scale,
  ShieldAlert,
  Trash2,
  Upload,
  WalletCards,
} from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import { getSchemeDetail, getSchemeFilters, getSchemes } from '../lib/api'
import { cache } from '../lib/cache'
import { biometricErrorMessage, supportsDeviceBiometrics } from '../lib/webauthn'
import type { SahayakProfile, SchemeDetail, SchemeFilters, SchemeSummary, UserType } from '../types/api'
import type { AppRoute } from '../types/navigation'
import { SchemeCardSkeleton } from './SkeletonLoader'

type Navigate = (route: AppRoute) => void
type Service = { icon: typeof Landmark; label: string; route: AppRoute; text: string }

const SERVICES: Service[] = [
  { icon: Landmark, label: 'Cooperative services', route: '/schemes', text: 'Explore member-focused support.' },
  { icon: ShieldAlert, label: 'PMFBY support', route: '/schemes', text: 'Prepare crop insurance questions.' },
  { icon: Scale, label: 'Cooperative laws', route: '/voice', text: 'Ask Sahayak in your own language.' },
  { icon: WalletCards, label: 'Financial literacy', route: '/voice', text: 'Understand everyday financial choices.' },
  { icon: MessageSquareWarning, label: 'Grievance support', route: '/grievances', text: 'Create a clear support draft.' },
  { icon: FileText, label: 'Documents', route: '/documents', text: 'Organise document conversations.' },
]

function profileName(profile: SahayakProfile): string {
  return profile.full_name?.split(/\s+/)[0] || 'there'
}

export function Dashboard({ profile, onNavigate, onOpenAuth }: { profile?: SahayakProfile | null; onNavigate: Navigate; onOpenAuth: () => void }) {
  const isGuest = !profile
  return (
    <main className="portal-page">
      <section className="dashboard-welcome">
        <div><p className="section-kicker">{isGuest ? 'Public service directory' : 'Your service space'}</p><h1>{profile ? `Welcome, ${profileName(profile)}.` : 'Explore Sahayak services.'}</h1><p>{isGuest ? 'Browse every service as a guest. Sign in only when you want personalised support.' : 'What would you like help understanding today?'}</p></div>
        <button className="primary-action" onClick={() => onNavigate('/voice')} type="button"><Mic size={18} /> Talk to Sahayak</button>
      </section>
      {isGuest && <p className="source-notice"><BookOpenCheck size={18} /> All public services are available to explore. Tell Sahayak your category for a more relevant scheme shortlist.</p>}
      <section className="voice-callout">
        <div className="voice-callout__orb"><Mic size={27} /></div>
        <div><span className="status-dot" /> Voice assistant ready<h2>Ask naturally. Receive guidance in your chosen language.</h2><p>Switch between all 10 supported languages from your voice workspace.</p></div>
        <button className="secondary-action" onClick={() => onNavigate('/voice')} type="button">Open voice assistant <ChevronRight size={16} /></button>
      </section>
      <section className="section-block"><div className="section-heading"><div><p className="section-kicker">Quick services</p><h2>Choose a place to begin.</h2></div></div>
        <div className="service-grid">{SERVICES.map(({ icon: Icon, label, route, text }) => <button className="service-card" key={label} onClick={() => onNavigate(route)} type="button"><span><Icon size={21} /></span><h3>{label}</h3><p>{text}</p><ChevronRight size={17} /></button>)}</div>
      </section>
      <section className="dashboard-lower">
        <div className="preview-card"><div><BookOpenCheck size={20} /><span className="preview-badge">Scheme guide</span></div><h3>{isGuest ? 'Find support for your category.' : 'Your relevant scheme guide.'}</h3><p>{isGuest ? 'Choose a category in the scheme directory, then ask Sahayak any eligibility or document question.' : 'Your profile category keeps the scheme directory focused on support relevant to you.'}</p><button onClick={() => onNavigate('/schemes')} type="button">View schemes <ChevronRight size={16} /></button></div>
        <div className="preview-card"><div><Bell size={20} /><span className="preview-badge">Preview</span></div><h3>Stay informed without the noise.</h3><p>Important updates and document reminders will be available in your notifications space.</p><button onClick={() => onNavigate('/notifications')} type="button">View notifications <ChevronRight size={16} /></button></div>
      </section>
      {isGuest && <p className="inline-notice">Sign in to save documents, receive notifications, and use a profile-based scheme shortlist. <button className="link-action" onClick={onOpenAuth} type="button">Sign in</button></p>}
    </main>
  )
}

type LocalDocument = { id: string; file: File; addedAt: string }

export function DocumentsView({ onTalk }: { onTalk: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [documents, setDocuments] = useState<LocalDocument[]>([])
  const [notice, setNotice] = useState<string | null>(null)
  function addDocument(event: ChangeEvent<HTMLInputElement>): void {
    const file = event.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) { setNotice('Choose a file that is 5 MB or smaller.'); return }
    setDocuments((items) => [{ id: crypto.randomUUID(), file, addedAt: new Date().toLocaleDateString() }, ...items])
    setNotice('Added for this browser session. Persistent document storage will be connected in a later phase.')
    event.target.value = ''
  }
  return (
    <main className="portal-page">
      <PageTitle eyebrow="Private documents" title="Your document centre." text="Use this space to organise documents and ask Sahayak about them." />
      <section className="document-upload-card"><div><span className="document-upload-card__icon"><Upload size={22} /></span><h2>Add a document</h2><p>PDF, DOCX, text and image files up to 5 MB. Files added here are session previews only until private storage is connected.</p></div><input accept=".pdf,.docx,.txt,.md,.jpg,.jpeg,.png" hidden onChange={addDocument} ref={inputRef} type="file" /><button className="primary-action" onClick={() => inputRef.current?.click()} type="button"><FilePlus2 size={17} /> Select document</button></section>
      {notice && <p className="inline-notice">{notice}</p>}
      <section className="section-block"><div className="section-heading"><div><p className="section-kicker">Session preview</p><h2>{documents.length ? 'Recent documents' : 'No documents yet.'}</h2></div><span className="preview-badge">Not saved</span></div>
        {documents.length ? <ul className="document-list">{documents.map((document) => <li key={document.id}><span className="document-list__icon"><FileText size={19} /></span><div><h3>{document.file.name}</h3><p>{Math.ceil(document.file.size / 1024)} KB · Added {document.addedAt}</p></div><button onClick={onTalk} type="button">Ask Sahayak</button><button aria-label={'Remove ' + document.file.name} className="header-icon-button" onClick={() => setDocuments((items) => items.filter((item) => item.id !== document.id))} type="button"><Trash2 size={17} /></button></li>)}</ul> : <EmptyState icon={FileText} text="Add a document when you are ready. You can also discuss a document directly with Sahayak AI." actionLabel="Ask Sahayak about a document" onAction={onTalk} />}
      </section>
    </main>
  )
}

const USER_TYPE_LABELS: Record<UserType, string> = {
  cooperative_member: 'Cooperative member',
  farmer: 'Farmer',
  pacs_member: 'PACS member',
  cooperative_official: 'Cooperative official',
  rural_stakeholder: 'Rural stakeholder',
  other: 'Other rural stakeholder',
}

export function SchemesView({ onTalk, profile }: { onTalk: () => void; profile?: SahayakProfile | null }) {
  const isGuest = !profile
  const [guestAudience, setGuestAudience] = useState<string>('')
  const [category, setCategory] = useState('')
  const [state, setState] = useState('')
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [filters, setFilters] = useState<SchemeFilters>({ categories: [], beneficiaries: [], states: [], types: [] })
  const [schemes, setSchemes] = useState<SchemeSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<SchemeDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const loadSchemes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getSchemes({
        query: submittedQuery,
        category: category || undefined,
        beneficiary: isGuest ? guestAudience || undefined : undefined,
        state: isGuest ? state || undefined : undefined,
        relevantToMe: !isGuest,
      })
      setSchemes(response.items)
      setTotal(response.total)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'We could not load the verified scheme directory.')
    } finally {
      setLoading(false)
    }
  }, [category, guestAudience, isGuest, state, submittedQuery])

  useEffect(() => {
    void getSchemeFilters().then(setFilters).catch(() => setFilters({ categories: [], beneficiaries: [], states: [], types: [] }))
  }, [])
  useEffect(() => { void loadSchemes() }, [loadSchemes])

  async function openScheme(scheme: SchemeSummary): Promise<void> {
    setDetailLoading(true)
    setSelected(null)
    try {
      setSelected(await getSchemeDetail(scheme.slug))
    } catch (detailError) {
      setError(detailError instanceof Error ? detailError.message : 'We could not open that scheme record.')
    } finally {
      setDetailLoading(false)
    }
  }

  const audienceLabel = profile?.user_type ? USER_TYPE_LABELS[profile.user_type] : 'your profile'
  return (
    <main className="portal-page">
      <PageTitle eyebrow="Scheme discovery" title={isGuest ? 'Find verified support for your situation.' : 'Your relevant verified schemes.'} text={isGuest ? 'Browse schemes, programmes and services discovered from Sahayak’s connected official sources. Choose your category or location to narrow the directory.' : `This directory is filtered using your Sahayak profile: ${audienceLabel}.`} />
      <section className="scheme-toolbar" aria-label="Scheme audience">
        <div><BookOpenCheck size={19} /><div><strong>{isGuest ? 'Guest scheme directory' : 'Personalised scheme directory'}</strong><p>{isGuest ? 'All currently verified records are available to browse. Tell Sahayak your category, state, crop or cooperative role for a focused shortlist.' : 'Your category and location are used only to surface potentially relevant records; they never guarantee eligibility.'}</p></div></div>
      </section>
      <form className="scheme-filters" onSubmit={(event) => { event.preventDefault(); setSubmittedQuery(query) }}>
        <input aria-label="Search verified schemes" maxLength={240} onChange={(event) => setQuery(event.target.value)} placeholder="Search support, insurance, credit or a scheme name" value={query} />
        <select aria-label="Scheme category" onChange={(event) => setCategory(event.target.value)} value={category}><option value="">All categories</option>{filters.categories.map((item) => <option key={item} value={item}>{item}</option>)}</select>
        {isGuest && <select aria-label="Your category" onChange={(event) => setGuestAudience(event.target.value)} value={guestAudience}><option value="">All beneficiary groups</option>{filters.beneficiaries.map((item) => <option key={item} value={item}>{USER_TYPE_LABELS[item as UserType] ?? item.replaceAll('_', ' ')}</option>)}</select>}
        {isGuest && <select aria-label="State" onChange={(event) => setState(event.target.value)} value={state}><option value="">All locations</option>{filters.states.map((item) => <option key={item} value={item}>{item}</option>)}</select>}
        <button className="secondary-action" type="submit">Search</button>
      </form>
      <p className="scheme-result-count" aria-live="polite">{loading ? 'Loading verified records…' : `${total} verified record${total === 1 ? '' : 's'} found`}</p>
      {error && <p className="inline-notice">{error}</p>}
      {!loading && <section className="scheme-grid">{schemes.map((scheme) => <article className="scheme-card scheme-card--catalogue" key={scheme.id}><span><BookOpenCheck size={21} /></span><p className="preview-badge">{scheme.category}</p><h2>{scheme.official_name}</h2><p>{scheme.description || 'Verified information is available in Sahayak AI.'}</p><dl><div><dt>For</dt><dd>{scheme.beneficiary_categories.length ? scheme.beneficiary_categories.map((item) => USER_TYPE_LABELS[item as UserType] ?? item.replaceAll('_', ' ')).join(', ') : 'See verified details'}</dd></div><div><dt>Coverage</dt><dd>{scheme.applicable_states.length ? scheme.applicable_states.join(', ') : scheme.geographic_scope === 'STATE' ? 'State-specific' : 'National / source-defined'}</dd></div><div><dt>Current status</dt><dd>{scheme.status === 'UNKNOWN' ? 'Current operational status not verified' : scheme.status.replaceAll('_', ' ')}</dd></div></dl><button className="link-action" onClick={() => void openScheme(scheme)} type="button">View details <ChevronRight size={15} /></button></article>)}</section>}
      {!loading && schemes.length === 0 && <EmptyState icon={BookOpenCheck} text="No verified record matches these filters yet. Ask Sahayak to narrow your need by category, state, crop, cooperative role or support type." actionLabel="Ask Sahayak" onAction={onTalk} />}
      {detailLoading && <p className="inline-notice">Opening verified scheme details…</p>}
      {selected && <SchemeDetailPanel scheme={selected} onAsk={onTalk} onClose={() => setSelected(null)} />}
    </main>
  )
}

function SchemeDetailPanel({ scheme, onAsk, onClose }: { scheme: SchemeDetail; onAsk: () => void; onClose: () => void }) {
  const dataValue = (key: string) => typeof scheme.data[key] === 'string' ? scheme.data[key] as string : null
  const fields = [
    ['What this is', dataValue('description')],
    ['Objective', dataValue('objective')],
    ['Who it may fit', dataValue('eligibility')],
    ['What it provides', dataValue('benefits')],
    ['Documents', dataValue('required_documents')],
    ['How to apply', dataValue('application_process')],
    ['Important dates', dataValue('important_dates')],
  ].filter((item): item is [string, string] => Boolean(item[1]))
  return <section className="scheme-detail-panel" aria-label="Verified scheme details"><div className="scheme-detail-panel__head"><div><p className="section-kicker">{scheme.scheme_type.replaceAll('_', ' ')}</p><h2>{scheme.official_name}</h2><p>Potential relevance is based on recorded source information. It is not an eligibility guarantee.</p></div><button className="header-icon-button" onClick={onClose} type="button" aria-label="Close details">×</button></div><div className="scheme-detail-panel__content">{fields.length ? fields.map(([label, value]) => <article key={label}><h3>{label}</h3><p>{value}</p></article>) : <p>Detailed fields have not yet been verified from the connected official record.</p>}</div><section className="scheme-detail-panel__sources"><h3>Verified information</h3><p>These source records support the information shown in Sahayak AI. You can ask Sahayak to explain any part here.</p><ul>{scheme.sources.map((source) => <li key={`${source.source_name}-${source.title}-${source.relevant_section}`}><strong>{source.source_name}</strong><span>{source.title}{source.relevant_section ? ` · ${source.relevant_section}` : ''}</span></li>)}</ul></section><button className="primary-action" onClick={onAsk} type="button">Ask Sahayak about this</button></section>
}

const NOTIFICATIONS = [
  { title: 'Welcome to Sahayak AI', text: 'Your notification space is ready. Personalised alerts will appear when connected to verified services.', date: 'Now', kind: 'Account' },
  { title: 'Scheme updates will be source-verified', text: 'We will not send unverified scheme information, legal changes or deadlines.', date: 'Preview', kind: 'Safety' },
]

export function NotificationsView() {
  return (
    <main className="portal-page"><PageTitle eyebrow="Notifications" title="Important updates, in one place." text="These are preview notifications. Live alerts will be added with the approved notification service." />
      <section className="notification-panel">{NOTIFICATIONS.map((item) => <article className="notification-item" key={item.title}><span className="notification-item__icon"><Bell size={18} /></span><div><p><b>{item.kind}</b><time>{item.date}</time></p><h2>{item.title}</h2><p>{item.text}</p></div><button aria-label={'More options for ' + item.title} className="header-icon-button" type="button"><MoreHorizontal size={18} /></button></article>)}</section>
    </main>
  )
}

export function GrievancesView() {
  const [notice, setNotice] = useState<string | null>(null)
  function submit(event: FormEvent<HTMLFormElement>): void { event.preventDefault(); setNotice('Your grievance draft is ready in this browser. Keep the facts and documents together here while Sahayak helps you improve it.') }
  return (
    <main className="portal-page"><PageTitle eyebrow="Grievance support" title="Prepare a clear request for help." text="Build a factual grievance draft, organise evidence and ask Sahayak to make the next step clear." />
      <div className="grievance-layout"><section className="grievance-form-card"><h2>Draft a grievance</h2><form onSubmit={submit}><label>Category<select required defaultValue=""><option disabled value="">Choose a category</option><option>Cooperative service</option><option>PACS service</option><option>Document support</option><option>Other</option></select></label><label>Describe what happened<textarea maxLength={1500} placeholder="Share the facts, relevant dates and the help you need." required rows={6} /></label><label>Supporting document <span className="field-optional">Preview only</span><input type="file" /></label><button className="primary-action" type="submit">Save draft</button></form>{notice && <p className="inline-notice">{notice}</p>}</section><aside className="grievance-side-note"><MessageSquareWarning size={22} /><h2>Make your case clear</h2><p>Keep dates, receipts, acknowledgements and previous messages together. Ask Sahayak AI to turn them into a concise description of the issue and the resolution you need.</p></aside></div>
    </main>
  )
}

export function ProfileView({ auth, profile }: { auth: SahayakAuth; profile: SahayakProfile }) {
  const [isEditing, setIsEditing] = useState(false)
  const [values, setValues] = useState({ full_name: profile.full_name ?? '', state: profile.state ?? '', district: profile.district ?? '', village_or_town: profile.village_or_town ?? '', address: profile.address ?? '', cooperative_role: profile.cooperative_role ?? '', user_type: profile.user_type ?? 'other' as UserType })
  const [notice, setNotice] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isUpdatingFaceId, setIsUpdatingFaceId] = useState(false)
  const [faceIdNotice, setFaceIdNotice] = useState<string | null>(null)
  const deviceBiometricsAvailable = supportsDeviceBiometrics()

  async function save(event: FormEvent<HTMLFormElement>): Promise<void> { event.preventDefault(); setIsSaving(true); setNotice(null); try { await auth.saveProfile(values); setNotice('Profile updated.'); setIsEditing(false) } catch (error) { setNotice(error instanceof Error ? error.message : 'We could not update your profile.') } finally { setIsSaving(false) } }

  async function updateFaceId(): Promise<void> {
    setFaceIdNotice(null)
    setIsUpdatingFaceId(true)
    try {
      if (profile.face_id_enabled) {
        await auth.removeFaceId()
        setFaceIdNotice('Face ID has been removed from this Sahayak account.')
      } else {
        await auth.registerFaceId()
        setFaceIdNotice('Face ID is ready for your next sign-in on this device.')
      }
    } catch (error) {
      setFaceIdNotice(biometricErrorMessage(error, 'We could not update Face ID. Please try again.'))
    } finally {
      setIsUpdatingFaceId(false)
    }
  }

  return (
    <main className="portal-page"><PageTitle eyebrow="Your profile" title="Your Sahayak details." text="Your verified mobile number is your account identity and cannot be edited here." />
      <section className="profile-card"><div className="profile-card__identity"><span>{profileName(profile).slice(0, 1).toUpperCase()}</span><div><h2>{profile.full_name || 'Complete your profile'}</h2><p>+91 {profile.phone_number.replace('+91', '')}</p></div><button className="secondary-action" onClick={() => setIsEditing((editing) => !editing)} type="button">{isEditing ? 'Cancel' : 'Edit profile'}</button></div>
        {isEditing ? <form className="profile-form" onSubmit={(event) => void save(event)}><div className="form-grid"><label>Name<input onChange={(event) => setValues({ ...values, full_name: event.target.value })} value={values.full_name} /></label><label>State<input onChange={(event) => setValues({ ...values, state: event.target.value })} value={values.state} /></label><label>District / city<input onChange={(event) => setValues({ ...values, district: event.target.value })} value={values.district} /></label><label>Town / village<input onChange={(event) => setValues({ ...values, village_or_town: event.target.value })} value={values.village_or_town} /></label></div><label>Address <span className="field-optional">Optional</span><textarea onChange={(event) => setValues({ ...values, address: event.target.value })} rows={3} value={values.address} /></label><div className="form-grid"><label>Your role<select onChange={(event) => setValues({ ...values, user_type: event.target.value as UserType })} value={values.user_type}><option value="cooperative_member">Cooperative member</option><option value="farmer">Farmer</option><option value="pacs_member">PACS member</option><option value="cooperative_official">Cooperative official</option><option value="rural_stakeholder">Rural stakeholder</option><option value="other">Other</option></select></label><label>Cooperative role <span className="field-optional">Optional</span><input onChange={(event) => setValues({ ...values, cooperative_role: event.target.value })} value={values.cooperative_role} /></label></div><button className="primary-action" disabled={isSaving} type="submit">{isSaving ? <LoaderCircle className="spin" size={17} /> : null}{isSaving ? 'Saving…' : 'Save changes'}</button></form> : <dl className="profile-details"><div><dt>State</dt><dd>{profile.state || '—'}</dd></div><div><dt>District / city</dt><dd>{profile.district || '—'}</dd></div><div><dt>Town / village</dt><dd>{profile.village_or_town || '—'}</dd></div><div><dt>Role</dt><dd>{profile.user_type?.replaceAll('_', ' ') || '—'}</dd></div><div><dt>Cooperative role</dt><dd>{profile.cooperative_role || '—'}</dd></div><div><dt>Address</dt><dd>{profile.address || '—'}</dd></div></dl>}
        {notice && <p className="inline-notice">{notice}</p>}
      </section>
      <section className="profile-security-card" aria-labelledby="face-id-heading">
        <span className="profile-security-card__icon"><Fingerprint size={23} /></span>
        <div>
          <p className="section-kicker">Sign-in security</p>
          <h2 id="face-id-heading">Face ID and device sign-in</h2>
          <p>{profile.face_id_enabled ? 'Face ID is enabled for this Sahayak account on a registered device.' : 'Set up Face ID, Touch ID, or your device screen lock for faster sign-in.'}</p>
          {!profile.face_id_enabled && <small>Your face data and private key remain on your device. Sahayak stores only a public credential.</small>}
          {!profile.face_id_enabled && !deviceBiometricsAvailable && <small className="profile-security-card__warning">Use a supported device over HTTPS to set up Face ID.</small>}
          {faceIdNotice && <p className="profile-security-card__feedback" role="status">{faceIdNotice}</p>}
        </div>
        {profile.face_id_enabled ? (
          <button className="secondary-action" disabled={isUpdatingFaceId} onClick={() => void updateFaceId()} type="button">{isUpdatingFaceId ? <LoaderCircle className="spin" size={16} /> : null}{isUpdatingFaceId ? 'Removing…' : 'Remove Face ID'}</button>
        ) : (
          <button className="primary-action" disabled={isUpdatingFaceId || !deviceBiometricsAvailable} onClick={() => void updateFaceId()} type="button">{isUpdatingFaceId ? <LoaderCircle className="spin" size={16} /> : <Fingerprint size={16} />}{isUpdatingFaceId ? 'Setting up…' : 'Set up Face ID'}</button>
        )}
      </section>
    </main>
  )
}

function PageTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) { return <header className="page-title"><p className="section-kicker">{eyebrow}</p><h1>{title}</h1><p>{text}</p></header> }
function EmptyState({ icon: Icon, text, actionLabel, onAction }: { icon: typeof FileText; text: string; actionLabel: string; onAction: () => void }) { return <div className="empty-state"><Icon size={28} /><p>{text}</p><button className="secondary-action" onClick={onAction} type="button">{actionLabel}</button></div> }
