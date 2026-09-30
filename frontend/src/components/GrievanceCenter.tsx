import { type FormEvent, useCallback, useEffect, useState } from 'react'
import {
  ArrowUpRight, CheckCircle2, ChevronRight, Clock3, ExternalLink, FileText,
  LoaderCircle, MessageSquareWarning, Plus, RefreshCw, Search, ShieldCheck,
} from 'lucide-react'

import {
  confirmGrievance, createGrievance, getGrievance, getGrievances, readyGrievance,
  recordOfficialHandoff, recordOfficialReference, updateGrievance,
} from '../lib/api'
import type { Grievance, GrievanceCategory, GrievanceDraftInput, GrievanceStatus, SahayakProfile } from '../types/api'

type DraftValues = {
  category: GrievanceCategory
  subject: string
  description: string
  organization: string
  state: string
  district: string
  locality: string
  incident_date: string
  amount_description: string
  has_contacted_organization: '' | 'yes' | 'no'
  prior_reference: string
}

const CATEGORIES: Array<{ value: GrievanceCategory; label: string }> = [
  { value: 'PACS_ISSUE', label: 'PACS issue' },
  { value: 'COOPERATIVE_SOCIETY', label: 'Cooperative society issue' },
  { value: 'PAYMENT', label: 'Payment issue' },
  { value: 'LOAN', label: 'Loan or credit issue' },
  { value: 'INSURANCE_CLAIM', label: 'Insurance or claim issue' },
  { value: 'GOVERNMENT_SCHEME', label: 'Government scheme issue' },
  { value: 'AGRICULTURE_SERVICE', label: 'Agriculture service issue' },
  { value: 'FINANCIAL_SERVICE', label: 'Financial service issue' },
  { value: 'DOCUMENT_CERTIFICATE', label: 'Document or certificate issue' },
  { value: 'ADMINISTRATIVE', label: 'Administrative issue' },
  { value: 'OTHER_GOVERNMENT', label: 'Other government service issue' },
]

const STATUS_COPY: Record<GrievanceStatus, string> = {
  DRAFT: 'Draft', READY_FOR_CONFIRMATION: 'Ready to review', USER_CONFIRMED: 'Confirmed',
  SUBMITTING: 'Submitting', SUBMITTED: 'Submitted', ACKNOWLEDGED: 'Acknowledged',
  UNDER_PROCESS: 'Under process', ACTION_REQUIRED: 'Action needed', RESOLVED: 'Resolved',
  CLOSED: 'Closed', ESCALATED: 'Escalated', APPEAL_AVAILABLE: 'Appeal available',
  APPEAL_SUBMITTED: 'Appeal submitted', SUBMISSION_FAILED: 'Submission failed', UNKNOWN: 'Status unknown',
}

function toDraftValues(grievance: Grievance | null, profile: SahayakProfile): DraftValues {
  return {
    category: grievance?.category ?? 'OTHER_GOVERNMENT',
    subject: grievance?.subject ?? '',
    description: grievance?.description ?? '',
    organization: grievance?.organization ?? '',
    state: grievance?.state ?? profile.state ?? '',
    district: grievance?.district ?? profile.district ?? '',
    locality: grievance?.locality ?? profile.village_or_town ?? '',
    incident_date: grievance?.incident_date ?? '',
    amount_description: grievance?.amount_description ?? '',
    has_contacted_organization: grievance?.has_contacted_organization === null || grievance?.has_contacted_organization === undefined
      ? '' : grievance.has_contacted_organization ? 'yes' : 'no',
    prior_reference: grievance?.prior_reference ?? '',
  }
}

function toPayload(values: DraftValues): GrievanceDraftInput {
  return {
    category: values.category,
    subject: values.subject || null,
    description: values.description || null,
    organization: values.organization || null,
    state: values.state || null,
    district: values.district || null,
    locality: values.locality || null,
    incident_date: values.incident_date || null,
    amount_description: values.amount_description || null,
    has_contacted_organization: values.has_contacted_organization === ''
      ? null : values.has_contacted_organization === 'yes',
    prior_reference: values.prior_reference || null,
  }
}

function dateTime(value: string | null): string {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function categoryLabel(category: GrievanceCategory): string {
  return CATEGORIES.find((item) => item.value === category)?.label ?? category.replaceAll('_', ' ')
}

export function GrievanceCenter({ profile, onTalk }: { profile: SahayakProfile; onTalk: () => void }) {
  const [items, setItems] = useState<Grievance[]>([])
  const [selected, setSelected] = useState<Grievance | null>(null)
  const [values, setValues] = useState<DraftValues>(() => toDraftValues(null, profile))
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<GrievanceStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [reference, setReference] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getGrievances({ state: filter || undefined, query })
      setItems(response.items)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'We could not load your grievances.')
    } finally {
      setLoading(false)
    }
  }, [filter, query])

  useEffect(() => { void load() }, [load])

  function setValue<Key extends keyof DraftValues>(key: Key, value: DraftValues[Key]): void {
    setValues((current) => ({ ...current, [key]: value }))
  }

  function storeInList(grievance: Grievance): void {
    setItems((current) => [grievance, ...current.filter((item) => item.id !== grievance.id)])
    setSelected(grievance)
  }

  async function open(grievance: Grievance): Promise<void> {
    setSaving(true)
    setError(null)
    try {
      const detail = await getGrievance(grievance.id)
      setSelected(detail)
      setValues(toDraftValues(detail, profile))
      setReference('')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (openError) {
      setError(openError instanceof Error ? openError.message : 'We could not open that grievance.')
    } finally {
      setSaving(false)
    }
  }

  function startNew(): void {
    setSelected(null)
    setValues(toDraftValues(null, profile))
    setReference('')
    setNotice(null)
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function saveDraft(): Promise<Grievance | null> {
    setSaving(true)
    setError(null)
    setNotice(null)
    try {
      const payload = toPayload(values)
      const grievance = selected
        ? await updateGrievance(selected.id, selected.version, payload)
        : await createGrievance(payload)
      storeInList(grievance)
      setValues(toDraftValues(grievance, profile))
      setNotice('Your draft is saved privately in Sahayak. It has not been submitted to any authority.')
      return grievance
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'We could not save the grievance draft.')
      return null
    } finally {
      setSaving(false)
    }
  }

  async function save(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    await saveDraft()
  }

  async function preparePreview(): Promise<void> {
    const draft = await saveDraft()
    if (!draft) return
    setSaving(true)
    setError(null)
    try {
      const preview = await readyGrievance(draft.id, draft.version)
      storeInList(preview)
      setNotice('Review every detail below. Sahayak has not submitted anything.')
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : 'We could not prepare the preview.')
    } finally {
      setSaving(false)
    }
  }

  async function confirm(): Promise<void> {
    if (!selected) return
    setSaving(true)
    setError(null)
    try {
      const confirmed = await confirmGrievance(selected.id, selected.version)
      storeInList(confirmed)
      setNotice('Your reviewed draft is confirmed. Continue to the official portal to lodge it yourself.')
    } catch (confirmError) {
      setError(confirmError instanceof Error ? confirmError.message : 'We could not record your confirmation.')
    } finally {
      setSaving(false)
    }
  }

  async function openOfficialHandoff(): Promise<void> {
    if (!selected) return
    try {
      const handoff = await recordOfficialHandoff(selected.id, selected.version)
      storeInList(handoff)
    } catch (handoffError) {
      // The browser still opens a verified public portal without sending it
      // any Sahayak data. Failing an audit update must not claim submission.
      setError(handoffError instanceof Error ? handoffError.message : 'The official portal opened, but we could not record that step.')
    }
  }

  async function addReference(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!selected || !reference.trim()) return
    setSaving(true)
    setError(null)
    try {
      const updated = await recordOfficialReference(selected.id, selected.version, reference)
      storeInList(updated)
      setReference('')
      setNotice('The official reference has been saved exactly as you entered it. Sahayak has not verified its status.')
    } catch (referenceError) {
      setError(referenceError instanceof Error ? referenceError.message : 'We could not save that reference.')
    } finally {
      setSaving(false)
    }
  }

  const isPreview = selected?.status === 'READY_FOR_CONFIRMATION'
  const isConfirmed = selected?.status === 'USER_CONFIRMED' || selected?.status === 'ACTION_REQUIRED'
  const isEditable = !selected || selected.status === 'DRAFT'

  return (
    <main className="portal-page grievance-page">
      <header className="grievance-page__header">
        <div><p className="section-kicker">Grievance support</p><h1>Report an issue. Stay informed.</h1><p>Tell us what happened in your own words. Review the complete draft before you decide whether to continue to the official grievance portal.</p></div>
        <button className="primary-action" onClick={startNew} type="button"><Plus size={17} /> File a grievance</button>
      </header>

      {error && <p className="grievance-feedback grievance-feedback--error" role="alert">{error}</p>}
      {notice && <p className="grievance-feedback" role="status">{notice}</p>}

      <section className="grievance-workspace" aria-label="Grievance workspace">
        <div className="grievance-editor">
          {isPreview && selected ? (
            <GrievancePreview grievance={selected} onConfirm={confirm} onEdit={() => { setSelected({ ...selected, status: 'DRAFT' }); setNotice('Edit the draft, then prepare a new preview.') }} saving={saving} />
          ) : isConfirmed && selected ? (
            <ConfirmedHandoff grievance={selected} onOpenOfficialHandoff={openOfficialHandoff} onAddReference={addReference} reference={reference} setReference={setReference} saving={saving} />
          ) : isEditable ? (
            <form className="grievance-form-card grievance-editor__card" onSubmit={(event) => void save(event)}>
              <div className="grievance-editor__heading"><div><h2>{selected ? 'Continue your draft' : 'Tell us what happened'}</h2><p>Only share facts you are comfortable providing. Do not include passwords, PINs, OTPs, or bank card details.</p></div><ShieldCheck size={22} aria-hidden="true" /></div>
              <div className="grievance-form-grid">
                <label className="grievance-field grievance-field--wide">What is a short title for this issue?<input autoComplete="off" maxLength={180} onChange={(event) => setValue('subject', event.target.value)} placeholder="For example: PACS payment not received" value={values.subject} /></label>
                <label className="grievance-field">Issue type<select onChange={(event) => setValue('category', event.target.value as GrievanceCategory)} value={values.category}>{CATEGORIES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
                <label className="grievance-field">PACS or organisation involved<input autoComplete="organization" maxLength={180} onChange={(event) => setValue('organization', event.target.value)} placeholder="Name, if known" value={values.organization} /></label>
                <label className="grievance-field grievance-field--wide">What happened?<textarea maxLength={6000} onChange={(event) => setValue('description', event.target.value)} placeholder="Describe the facts, relevant dates and the help you need." required rows={6} value={values.description} /></label>
                <label className="grievance-field">State<input autoComplete="address-level1" maxLength={100} onChange={(event) => setValue('state', event.target.value)} placeholder="Your state" value={values.state} /></label>
                <label className="grievance-field">District<input autoComplete="address-level2" maxLength={120} onChange={(event) => setValue('district', event.target.value)} placeholder="District, if known" value={values.district} /></label>
                <label className="grievance-field">When did this happen?<input max={new Date().toISOString().slice(0, 10)} onChange={(event) => setValue('incident_date', event.target.value)} type="date" value={values.incident_date} /></label>
                <label className="grievance-field">Amount, if relevant<input inputMode="decimal" maxLength={80} onChange={(event) => setValue('amount_description', event.target.value)} placeholder="For example: about ₹5,000" value={values.amount_description} /></label>
                <label className="grievance-field">Have you already contacted them?<select onChange={(event) => setValue('has_contacted_organization', event.target.value as DraftValues['has_contacted_organization'])} value={values.has_contacted_organization}><option value="">I do not know / not applicable</option><option value="yes">Yes</option><option value="no">No</option></select></label>
                <label className="grievance-field">Earlier complaint number<input maxLength={120} onChange={(event) => setValue('prior_reference', event.target.value)} placeholder="If you have one" value={values.prior_reference} /></label>
              </div>
              <div className="grievance-editor__actions"><button className="secondary-action" disabled={saving} type="submit">{saving ? <LoaderCircle className="spin" size={16} /> : <FileText size={16} />}{selected ? 'Save changes' : 'Save draft'}</button><button className="primary-action" disabled={saving} onClick={() => void preparePreview()} type="button">Review complete grievance <ChevronRight size={16} /></button></div>
              <p className="grievance-editor__note">Supporting files are never uploaded automatically. Keep documents with you and add them only in the official portal when it provides a secure upload option.</p>
            </form>
          ) : null}
        </div>

        <aside className="grievance-guidance"><MessageSquareWarning size={22} /><h2>Prefer to speak?</h2><p>Tell Sahayak what happened in the language you prefer. It can help you organise the facts and explain the next step.</p><button className="secondary-action" onClick={onTalk} type="button">Talk to Sahayak <ChevronRight size={16} /></button><hr /><h3>What Sahayak does</h3><ul><li>Prepares and saves your private draft</li><li>Shows a complete preview before confirmation</li><li>Links only to a verified official handoff</li></ul><p className="grievance-guidance__fineprint">Sahayak does not submit a complaint or confirm an official status unless an authorised integration is configured.</p></aside>
      </section>

      <section className="grievance-history" aria-labelledby="grievance-history-title">
        <div className="grievance-history__heading"><div><p className="section-kicker">Your records</p><h2 id="grievance-history-title">Your grievance journey</h2><p>Official status is only current when it was checked through an authorised source. This deployment provides a secure official handoff, not status polling.</p></div><button aria-label="Refresh grievances" className="header-icon-button" disabled={loading} onClick={() => void load()} type="button"><RefreshCw className={loading ? 'spin' : ''} size={17} /></button></div>
        <div className="grievance-history__filters"><label><Search size={16} /><span className="sr-only">Search grievances</span><input onChange={(event) => setQuery(event.target.value)} placeholder="Search title or reference" value={query} /></label><select aria-label="Filter grievances by status" onChange={(event) => setFilter(event.target.value as GrievanceStatus | '')} value={filter}><option value="">All statuses</option>{Object.entries(STATUS_COPY).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        {loading ? <p className="grievance-loading"><LoaderCircle className="spin" size={18} /> Loading your records…</p> : items.length === 0 ? <div className="grievance-empty"><MessageSquareWarning size={28} /><h3>Your grievance journey starts here.</h3><p>Report an issue, track its progress, and stay informed from one place.</p><button className="primary-action" onClick={startNew} type="button">File a grievance</button></div> : <div className="grievance-list">{items.map((item) => <article key={item.id}><div className="grievance-list__status"><span className={`grievance-status grievance-status--${item.status.toLowerCase()}`}>{STATUS_COPY[item.status]}</span><time>{dateTime(item.updated_at)}</time></div><div><h3>{item.subject || 'Untitled grievance draft'}</h3><p>{categoryLabel(item.category)}{item.organization ? ` · ${item.organization}` : ''}</p><small>Sahayak ID: {item.id}</small>{item.official_reference && <small>Official reference: {item.official_reference} <em>(member reported)</em></small>}</div><button className="secondary-action" onClick={() => void open(item)} type="button">View <ChevronRight size={16} /></button></article>)}</div>}
      </section>
    </main>
  )
}

function GrievancePreview({ grievance, onConfirm, onEdit, saving }: { grievance: Grievance; onConfirm: () => Promise<void>; onEdit: () => void; saving: boolean }) {
  return <section className="grievance-preview"><div className="grievance-preview__heading"><div><p className="section-kicker">Grievance preview</p><h2>Check every detail before confirming.</h2><p>Sahayak will not send this complaint to any authority.</p></div><CheckCircle2 size={28} aria-hidden="true" /></div><dl><div><dt>Subject</dt><dd>{grievance.subject}</dd></div><div><dt>Category</dt><dd>{categoryLabel(grievance.category)}</dd></div><div><dt>Authority</dt><dd>{grievance.authority_name}</dd></div><div><dt>Location</dt><dd>{[grievance.district, grievance.state].filter(Boolean).join(', ')}</dd></div><div className="grievance-preview__description"><dt>What happened</dt><dd>{grievance.description}</dd></div><div><dt>Official handoff</dt><dd>{grievance.destination_name}</dd></div></dl><p className="grievance-preview__notice">When you confirm, Sahayak records your confirmation. You will then choose whether to open the official portal and lodge the grievance yourself.</p><div className="grievance-editor__actions"><button className="secondary-action" disabled={saving} onClick={onEdit} type="button">Edit draft</button><button className="primary-action" disabled={saving} onClick={() => void onConfirm()} type="button">I confirm this grievance is correct <CheckCircle2 size={16} /></button></div></section>
}

function ConfirmedHandoff({ grievance, onOpenOfficialHandoff, onAddReference, reference, setReference, saving }: { grievance: Grievance; onOpenOfficialHandoff: () => Promise<void>; onAddReference: (event: FormEvent<HTMLFormElement>) => Promise<void>; reference: string; setReference: (value: string) => void; saving: boolean }) {
  const isOpened = grievance.status === 'ACTION_REQUIRED'
  return <section className="grievance-confirmed"><div><CheckCircle2 size={28} aria-hidden="true" /><p className="section-kicker">{isOpened ? 'Official action needed' : 'Draft confirmed'}</p><h2>{isOpened ? 'Complete your grievance in the official portal.' : 'Your review is recorded.'}</h2><p>{isOpened ? 'Sahayak did not send your complaint. Complete the form in the official portal and keep its acknowledgement number.' : 'Sahayak has not sent anything. The next step is your choice: open the verified official portal and lodge the complaint yourself.'}</p></div>{grievance.destination_url && <a className="primary-action" href={grievance.destination_url} onClick={() => void onOpenOfficialHandoff()} rel="noreferrer" target="_blank">Open official portal <ExternalLink size={16} /></a>}<div className="grievance-confirmed__links">{grievance.official_tracking_url && <a href={grievance.official_tracking_url} rel="noreferrer" target="_blank">View official status <ArrowUpRight size={14} /></a>}<span><Clock3 size={14} /> Confirmed {dateTime(grievance.confirmed_at)}</span></div>{isOpened && !grievance.official_reference && <form className="grievance-reference-form" onSubmit={(event) => void onAddReference(event)}><label>Save the acknowledgement number you receive<input maxLength={160} onChange={(event) => setReference(event.target.value)} placeholder="Enter it exactly as shown" required value={reference} /></label><button className="secondary-action" disabled={saving} type="submit">Save official reference</button></form>}{grievance.official_reference && <p className="grievance-reference-saved"><ShieldCheck size={17} /> Official reference: <strong>{grievance.official_reference}</strong><span>Recorded from your entry; not independently verified.</span></p>}</section>
}
