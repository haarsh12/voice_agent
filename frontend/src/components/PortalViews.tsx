import { type ChangeEvent, type FormEvent, useRef, useState } from 'react'
import {
  Bell,
  BookOpenCheck,
  ChevronRight,
  FilePlus2,
  FileText,
  Landmark,
  Leaf,
  LoaderCircle,
  MessageSquareWarning,
  Mic,
  MoreHorizontal,
  Scale,
  ShieldAlert,
  Trash2,
  Upload,
  UserRound,
  WalletCards,
} from 'lucide-react'

import type { SahayakAuth } from '../hooks/useAuth'
import type { SahayakProfile, UserType } from '../types/api'
import type { AppRoute } from '../types/navigation'

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

export function Dashboard({ profile, onNavigate }: { profile: SahayakProfile; onNavigate: Navigate }) {
  return (
    <main className="portal-page">
      <section className="dashboard-welcome">
        <div><p className="section-kicker">Your service space</p><h1>Welcome, {profileName(profile)}.</h1><p>What would you like help understanding today?</p></div>
        <button className="primary-action" onClick={() => onNavigate('/voice')} type="button"><Mic size={18} /> Talk to Sahayak</button>
      </section>
      <section className="voice-callout">
        <div className="voice-callout__orb"><Mic size={27} /></div>
        <div><span className="status-dot" /> Voice assistant ready<h2>Ask naturally. Receive guidance in your chosen language.</h2><p>Switch between all 10 supported languages from your voice workspace.</p></div>
        <button className="secondary-action" onClick={() => onNavigate('/voice')} type="button">Open voice assistant <ChevronRight size={16} /></button>
      </section>
      <section className="section-block"><div className="section-heading"><div><p className="section-kicker">Quick services</p><h2>Choose a place to begin.</h2></div></div>
        <div className="service-grid">{SERVICES.map(({ icon: Icon, label, route, text }) => <button className="service-card" key={label} onClick={() => onNavigate(route)} type="button"><span><Icon size={21} /></span><h3>{label}</h3><p>{text}</p><ChevronRight size={17} /></button>)}</div>
      </section>
      <section className="dashboard-lower">
        <div className="preview-card"><div><BookOpenCheck size={20} /><span className="preview-badge">Preview</span></div><h3>Suggested support will appear here.</h3><p>Personalised scheme information will only be shown after the verified knowledge base is connected.</p><button onClick={() => onNavigate('/schemes')} type="button">View scheme space <ChevronRight size={16} /></button></div>
        <div className="preview-card"><div><Bell size={20} /><span className="preview-badge">Preview</span></div><h3>Stay informed without the noise.</h3><p>Important updates and document reminders will be available in your notifications space.</p><button onClick={() => onNavigate('/notifications')} type="button">View notifications <ChevronRight size={16} /></button></div>
      </section>
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

const SCHEME_CATEGORIES = [
  { icon: Leaf, title: 'Agriculture', summary: 'Official agriculture-support content will be added after source verification.' },
  { icon: ShieldAlert, title: 'Crop insurance', summary: 'PMFBY guidance will cite the current official source and jurisdiction.' },
  { icon: Landmark, title: 'Cooperative', summary: 'Member services and cooperative-programme guidance will be verified before publishing.' },
  { icon: WalletCards, title: 'Financial assistance', summary: 'Financial-awareness information will be educational and source-grounded.' },
  { icon: UserRound, title: 'Member services', summary: 'Your eligible local services will appear once the verified data layer is ready.' },
]

export function SchemesView({ onTalk }: { onTalk: () => void }) {
  return (
    <main className="portal-page">
      <PageTitle eyebrow="Scheme discovery" title="Find trusted support, clearly." text="This preview deliberately does not invent eligibility, benefits, deadlines or requirements. Verified official sources will be connected next." />
      <p className="source-notice"><BookOpenCheck size={18} /> Official knowledge source connection pending — all cards below are placeholders.</p>
      <section className="scheme-grid">{SCHEME_CATEGORIES.map(({ icon: Icon, title, summary }) => <article className="scheme-card" key={title}><span><Icon size={21} /></span><p className="preview-badge">Preview category</p><h2>{title}</h2><p>{summary}</p><dl><div><dt>Eligibility</dt><dd>Verified details forthcoming</dd></div><div><dt>Documents</dt><dd>Verified details forthcoming</dd></div></dl><button className="link-action" onClick={onTalk} type="button">Ask a general question <ChevronRight size={15} /></button></article>)}</section>
    </main>
  )
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
  function submit(event: FormEvent<HTMLFormElement>): void { event.preventDefault(); setNotice('Your draft remains only in this browser. Government grievance submission will be enabled after an authorised backend integration is available.') }
  return (
    <main className="portal-page"><PageTitle eyebrow="Grievance support" title="Prepare a clear request for help." text="This is a private draft tool, not an official grievance submission channel." />
      <div className="grievance-layout"><section className="grievance-form-card"><h2>Draft a grievance</h2><form onSubmit={submit}><label>Category<select required defaultValue=""><option disabled value="">Choose a category</option><option>Cooperative service</option><option>PACS service</option><option>Document support</option><option>Other</option></select></label><label>Describe what happened<textarea maxLength={1500} placeholder="Share the facts, relevant dates and the help you need." required rows={6} /></label><label>Supporting document <span className="field-optional">Preview only</span><input type="file" /></label><button className="primary-action" type="submit">Save draft</button></form>{notice && <p className="inline-notice">{notice}</p>}</section><aside className="grievance-side-note"><MessageSquareWarning size={22} /><h2>Before you submit anywhere</h2><p>Keep a copy of relevant documents and ask Sahayak AI to help you make your description clear. Official escalation pathways will be added only after verification.</p></aside></div>
    </main>
  )
}

export function ProfileView({ auth, profile }: { auth: SahayakAuth; profile: SahayakProfile }) {
  const [isEditing, setIsEditing] = useState(false)
  const [values, setValues] = useState({ full_name: profile.full_name ?? '', state: profile.state ?? '', district: profile.district ?? '', village_or_town: profile.village_or_town ?? '', address: profile.address ?? '', cooperative_role: profile.cooperative_role ?? '', user_type: profile.user_type ?? 'other' as UserType })
  const [notice, setNotice] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  async function save(event: FormEvent<HTMLFormElement>): Promise<void> { event.preventDefault(); setIsSaving(true); setNotice(null); try { await auth.saveProfile(values); setNotice('Profile updated.'); setIsEditing(false) } catch (error) { setNotice(error instanceof Error ? error.message : 'We could not update your profile.') } finally { setIsSaving(false) } }
  return (
    <main className="portal-page"><PageTitle eyebrow="Your profile" title="Your Sahayak details." text="Your verified mobile number is your account identity and cannot be edited here." />
      <section className="profile-card"><div className="profile-card__identity"><span>{profileName(profile).slice(0, 1).toUpperCase()}</span><div><h2>{profile.full_name || 'Complete your profile'}</h2><p>+91 {profile.phone_number.replace('+91', '')}</p></div><button className="secondary-action" onClick={() => setIsEditing((editing) => !editing)} type="button">{isEditing ? 'Cancel' : 'Edit profile'}</button></div>
        {isEditing ? <form className="profile-form" onSubmit={(event) => void save(event)}><div className="form-grid"><label>Name<input onChange={(event) => setValues({ ...values, full_name: event.target.value })} value={values.full_name} /></label><label>State<input onChange={(event) => setValues({ ...values, state: event.target.value })} value={values.state} /></label><label>District / city<input onChange={(event) => setValues({ ...values, district: event.target.value })} value={values.district} /></label><label>Town / village<input onChange={(event) => setValues({ ...values, village_or_town: event.target.value })} value={values.village_or_town} /></label></div><label>Address <span className="field-optional">Optional</span><textarea onChange={(event) => setValues({ ...values, address: event.target.value })} rows={3} value={values.address} /></label><div className="form-grid"><label>Your role<select onChange={(event) => setValues({ ...values, user_type: event.target.value as UserType })} value={values.user_type}><option value="cooperative_member">Cooperative member</option><option value="farmer">Farmer</option><option value="pacs_member">PACS member</option><option value="cooperative_official">Cooperative official</option><option value="rural_stakeholder">Rural stakeholder</option><option value="other">Other</option></select></label><label>Cooperative role <span className="field-optional">Optional</span><input onChange={(event) => setValues({ ...values, cooperative_role: event.target.value })} value={values.cooperative_role} /></label></div><button className="primary-action" disabled={isSaving} type="submit">{isSaving ? <LoaderCircle className="spin" size={17} /> : null}{isSaving ? 'Saving…' : 'Save changes'}</button></form> : <dl className="profile-details"><div><dt>State</dt><dd>{profile.state || '—'}</dd></div><div><dt>District / city</dt><dd>{profile.district || '—'}</dd></div><div><dt>Town / village</dt><dd>{profile.village_or_town || '—'}</dd></div><div><dt>Role</dt><dd>{profile.user_type?.replaceAll('_', ' ') || '—'}</dd></div><div><dt>Cooperative role</dt><dd>{profile.cooperative_role || '—'}</dd></div><div><dt>Address</dt><dd>{profile.address || '—'}</dd></div></dl>}
        {notice && <p className="inline-notice">{notice}</p>}
      </section>
    </main>
  )
}

function PageTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) { return <header className="page-title"><p className="section-kicker">{eyebrow}</p><h1>{title}</h1><p>{text}</p></header> }
function EmptyState({ icon: Icon, text, actionLabel, onAction }: { icon: typeof FileText; text: string; actionLabel: string; onAction: () => void }) { return <div className="empty-state"><Icon size={28} /><p>{text}</p><button className="secondary-action" onClick={onAction} type="button">{actionLabel}</button></div> }
