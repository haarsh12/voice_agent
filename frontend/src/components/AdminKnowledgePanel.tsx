import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { Database, ExternalLink, FileText, LoaderCircle, LogOut, RefreshCw, Server, ShieldCheck } from 'lucide-react'

import { endAdminSession, getAdminKnowledgeDashboard, getAdminSession, startAdminSession } from '../lib/api'
import type { AdminKnowledgeDashboard, AdminKnowledgeSource } from '../types/api'

function formatTime(value: string | null): string {
  if (!value) return 'Not recorded yet'
  const timestamp = new Date(value)
  return Number.isNaN(timestamp.getTime())
    ? 'Not recorded yet'
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(timestamp)
}

function sourceStatus(source: AdminKnowledgeSource): string {
  if (!source.enabled) return 'Disabled'
  if (source.validation_status === 'APPROVED') return 'Approved'
  if (source.validation_status === 'CHECK_FAILED') return 'Check needs attention'
  return 'Review required'
}

export function AdminKnowledgePanel() {
  const [adminId, setAdminId] = useState('')
  const [password, setPassword] = useState('')
  const [authenticated, setAuthenticated] = useState(false)
  const [dashboard, setDashboard] = useState<AdminKnowledgeDashboard | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDashboard = useCallback(async (): Promise<void> => {
    setIsRefreshing(true)
    setError(null)
    try {
      setDashboard(await getAdminKnowledgeDashboard())
    } catch (caughtError) {
      setAuthenticated(false)
      setDashboard(null)
      setError(caughtError instanceof Error ? caughtError.message : 'The knowledge dashboard could not be loaded.')
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    void getAdminSession()
      .then((session) => {
        if (!active || !session.authenticated) return
        setAuthenticated(true)
        return loadDashboard()
      })
      .catch(() => {
        // An absent admin cookie is expected on first visit; do not reveal it
        // as an error or reveal anything about admin account configuration.
      })
      .finally(() => {
        if (active) setIsChecking(false)
      })
    return () => { active = false }
  }, [loadDashboard])

  async function submitLogin(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    try {
      const session = await startAdminSession(adminId.trim(), password)
      setPassword('')
      setAuthenticated(session.authenticated)
      await loadDashboard()
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Administrator sign-in failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function logout(): Promise<void> {
    setError(null)
    try {
      await endAdminSession()
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Administrator sign-out failed.')
      return
    }
    setAuthenticated(false)
    setDashboard(null)
    setAdminId('')
    setPassword('')
  }

  if (isChecking) {
    return <main className="page-loader"><LoaderCircle className="spin" size={20} /> Checking administrator session…</main>
  }

  if (!authenticated || !dashboard) {
    return (
      <main className="admin-access-page">
        <section className="admin-access-card" aria-labelledby="admin-access-title">
          <span className="admin-access-card__icon" aria-hidden="true"><ShieldCheck size={27} /></span>
          <p className="section-kicker">Restricted area</p>
          <h1 id="admin-access-title">Knowledge operations</h1>
          <p>Sign in to inspect source checks, ingestion records, document versions, and vector-index health.</p>
          <form className="admin-login-form" onSubmit={(event) => void submitLogin(event)}>
            <label>
              Administrator ID
              <input autoComplete="username" maxLength={64} onChange={(event) => setAdminId(event.target.value)} required value={adminId} />
            </label>
            <label>
              Password
              <input autoComplete="current-password" maxLength={256} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
            </label>
            <button className="primary-action" disabled={isSubmitting} type="submit">
              {isSubmitting ? <LoaderCircle className="spin" size={18} /> : <ShieldCheck size={18} />}
              {isSubmitting ? 'Signing in…' : 'Open admin dashboard'}
            </button>
          </form>
          {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
          <p className="admin-access-card__note">This view shows operational metadata only. Source text, embeddings, API keys, and member data remain private.</p>
        </section>
      </main>
    )
  }

  return (
    <main className="admin-page">
      <header className="admin-page__header">
        <div>
          <p className="section-kicker">Restricted knowledge administration</p>
          <h1>Knowledge operations</h1>
          <p>Official source health, extracted-document records, and the private retrieval index.</p>
        </div>
        <div className="admin-page__actions">
          <button className="secondary-action" disabled={isRefreshing} onClick={() => void loadDashboard()} type="button">
            <RefreshCw className={isRefreshing ? 'spin' : ''} size={16} /> Refresh
          </button>
          <button className="admin-logout-button" onClick={() => void logout()} type="button"><LogOut size={16} /> Sign out</button>
        </div>
      </header>

      {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}

      <section className="admin-metric-grid" aria-label="Knowledge storage summary">
        <article><Database size={20} /><span>Official sources</span><strong>{dashboard.storage.source_count}</strong><small>Reviewed source groups</small></article>
        <article><FileText size={20} /><span>Current documents</span><strong>{dashboard.storage.current_document_count}</strong><small>{dashboard.storage.document_count} retained versions</small></article>
        <article><Server size={20} /><span>Knowledge chunks</span><strong>{dashboard.storage.chunk_count.toLocaleString()}</strong><small>Relational audit records</small></article>
        <article><Database size={20} /><span>Vector index</span><strong>{dashboard.storage.vector_index === 'connected' ? 'Connected' : dashboard.storage.vector_index}</strong><small>{dashboard.storage.vector_point_count?.toLocaleString() ?? '—'} private Qdrant points</small></article>
      </section>

      <section className="admin-section" aria-labelledby="source-health-title">
        <div className="admin-section__header">
          <div><p className="section-kicker">Approved source registry</p><h2 id="source-health-title">Source health and update history</h2></div>
          <span>Generated {formatTime(dashboard.generated_at)}</span>
        </div>
        <div className="admin-source-grid">
          {dashboard.sources.map((source) => (
            <article className="admin-source-card" key={source.key}>
              <div className="admin-source-card__heading"><div><h3>{source.name}</h3><p>{source.category.replaceAll('_', ' ')} · {source.geographic_scope.toLowerCase()}</p></div><span className={`admin-status admin-status--${source.validation_status.toLowerCase()}`}>{sourceStatus(source)}</span></div>
              <dl><div><dt>Current docs</dt><dd>{source.current_document_count}</dd></div><div><dt>Chunks</dt><dd>{source.chunk_count}</dd></div><div><dt>Check cycle</dt><dd>{source.check_interval_hours}h</dd></div><div><dt>Latest result</dt><dd>{source.latest_check?.result ?? 'Not checked'}</dd></div></dl>
              <p className="admin-source-card__time">Last successful check: {formatTime(source.last_successful_check_at)}</p>
              <p className="admin-source-card__time">Last ingestion: {formatTime(source.last_successful_ingestion_at)}</p>
              {source.latest_check && <p className="admin-source-card__time">Latest run: {source.latest_check.checked_documents} checked · {source.latest_check.changed_documents} changed</p>}
              <div className="admin-source-card__links">
                {source.entry_urls.map((url) => <a href={url} key={url} rel="noreferrer" target="_blank"><span>{new URL(url).hostname}</span><ExternalLink size={14} /></a>)}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="admin-section" aria-labelledby="recent-documents-title">
        <div className="admin-section__header"><div><p className="section-kicker">Extracted official documents</p><h2 id="recent-documents-title">Recently checked document versions</h2></div><span>{dashboard.recent_documents.length} shown</span></div>
        <div className="admin-document-table-wrap">
          <table className="admin-document-table">
            <thead><tr><th>Source</th><th>Document</th><th>Status</th><th>Extraction</th><th>Last checked</th></tr></thead>
            <tbody>{dashboard.recent_documents.map((document) => (
              <tr key={`${document.url}-${document.version_number}`}>
                <td>{document.source_name}</td>
                <td><a href={document.url} rel="noreferrer" target="_blank">{document.title}<ExternalLink size={13} /></a><small>Version {document.version_number}</small></td>
                <td><span className={`admin-status admin-status--${document.status.toLowerCase()}`}>{document.status}</span></td>
                <td>{document.extraction_method ?? 'Not recorded'}{document.is_ocr ? ' · OCR' : ''}</td>
                <td>{formatTime(document.last_checked_at)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    </main>
  )
}
