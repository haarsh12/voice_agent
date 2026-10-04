import { useCallback, useEffect, useState } from 'react'
import { Database, ExternalLink, FileText, RefreshCw, Server } from 'lucide-react'

import { getKnowledgeBaseStatus } from '../lib/api'
import { cache } from '../lib/cache'
import type { KnowledgeBaseSource, KnowledgeBaseStatus } from '../types/api'
import { KnowledgeSourceCardSkeleton, MetricCardSkeleton } from './SkeletonLoader'

function formatTime(value: string | null): string {
  if (!value) return 'Not recorded yet'
  const timestamp = new Date(value)
  return Number.isNaN(timestamp.getTime())
    ? 'Not recorded yet'
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(timestamp)
}

function sourceStatus(source: KnowledgeBaseSource): string {
  if (source.validation_status === 'APPROVED') return 'Approved'
  if (source.validation_status === 'CHECK_FAILED') return 'Check needs attention'
  if (source.validation_status === 'DISABLED') return 'Disabled'
  return 'Review required'
}

function coverageStatus(source: KnowledgeBaseSource): string {
  if (source.coverage_state === 'COMPLETE') return 'Coverage complete'
  if (source.coverage_state === 'PARTIAL') return 'Coverage partial'
  if (source.coverage_state === 'INCOMPLETE') return 'Coverage incomplete'
  return 'Coverage unknown'
}

function readableCategory(category: string): string {
  return category.replaceAll('_', ' ')
}

function safeHostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return 'Official source'
  }
}

/** Public provenance view. It exposes verified source metadata, never raw content or secrets. */
export function KnowledgeBasePanel() {
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAllSources, setShowAllSources] = useState(false)
  const [showAllDocuments, setShowAllDocuments] = useState(false)

  const loadKnowledgeBase = useCallback(async (refresh = false): Promise<void> => {
    if (refresh) setIsRefreshing(true)
    else setIsLoading(true)
    setError(null)
    try {
      setKnowledgeBase(await getKnowledgeBaseStatus(!refresh)) // Use cache unless refresh
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Knowledge Base could not be loaded.')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => { void loadKnowledgeBase() }, [loadKnowledgeBase])
  
  function clearCacheAndRefresh(): void {
    cache.clear()
    void loadKnowledgeBase(true)
  }

  if (isLoading) {
    return (
      <main className="knowledge-base-page">
        <header className="knowledge-base-page__header">
          <div>
            <p className="section-kicker">Public transparency</p>
            <h1>Knowledge Base</h1>
          </div>
        </header>
        <section className="knowledge-base-metric-grid" aria-label="Knowledge Base summary">
          {Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)}
        </section>
        <section className="knowledge-base-section">
          <div className="knowledge-base-section__header">
            <div><p className="section-kicker">Approved source registry</p><h2>Source health and update history</h2></div>
          </div>
          <div className="knowledge-base-source-grid">
            {Array.from({ length: 3 }).map((_, i) => <KnowledgeSourceCardSkeleton key={i} />)}
          </div>
        </section>
      </main>
    )
  }

  if (!knowledgeBase) {
    return (
      <main className="knowledge-base-page">
        <section className="knowledge-base-empty">
          <h1>Knowledge Base</h1>
          <p className="form-feedback form-feedback--error" role="alert">{error ?? 'Knowledge Base is unavailable.'}</p>
          <button className="primary-action" onClick={() => void loadKnowledgeBase()} type="button">Try again</button>
        </section>
      </main>
    )
  }

  const visibleSources = showAllSources ? knowledgeBase.sources : knowledgeBase.sources.slice(0, 6)
  const visibleDocuments = showAllDocuments ? knowledgeBase.recent_documents : knowledgeBase.recent_documents.slice(0, 10)

  return (
    <main className="knowledge-base-page">
      <header className="knowledge-base-page__header">
        <div>
          <p className="section-kicker">Public transparency</p>
          <h1>Knowledge Base</h1>
          <p>Reviewed official sources, current document records, and explicit coverage status. A successful check is not treated as complete knowledge.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="link-action" onClick={clearCacheAndRefresh} type="button">Clear cache</button>
          <button className="secondary-action" disabled={isRefreshing} onClick={() => void loadKnowledgeBase(true)} type="button">
            <RefreshCw className={isRefreshing ? 'spin' : ''} size={16} /> Refresh
          </button>
        </div>
      </header>

      {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}

      <section className="knowledge-base-metric-grid" aria-label="Knowledge Base summary">
        <article><Database size={20} /><span>Official sources</span><strong>{knowledgeBase.storage.source_count}</strong><small>Reviewed source groups</small></article>
        <article><FileText size={20} /><span>Current documents</span><strong>{knowledgeBase.storage.current_document_count}</strong><small>{knowledgeBase.storage.document_count} retained versions</small></article>
        <article><Server size={20} /><span>Knowledge chunks</span><strong>{knowledgeBase.storage.chunk_count.toLocaleString()}</strong><small>Extraction audit records</small></article>
        <article><Database size={20} /><span>Vector index</span><strong>{knowledgeBase.storage.vector_index === 'connected' ? 'Ready' : knowledgeBase.storage.vector_index}</strong><small>{knowledgeBase.storage.vector_point_count?.toLocaleString() ?? '—'} indexed points</small></article>
      </section>

      <section className="knowledge-base-section" aria-labelledby="source-health-title">
        <div className="knowledge-base-section__header">
          <div><p className="section-kicker">Approved source registry</p><h2 id="source-health-title">Source health and update history</h2></div>
          <span>Updated {formatTime(knowledgeBase.generated_at)} · {knowledgeBase.sources.length} sources</span>
        </div>
        <div className="knowledge-base-source-grid">
          {visibleSources.map((source) => (
            <article className="knowledge-base-source-card" key={source.key}>
              <div className="knowledge-base-source-card__heading"><div><h3>{source.name}</h3><p>{readableCategory(source.category)} · {source.geographic_scope.toLowerCase()}</p></div><div className="knowledge-base-source-card__status-stack"><span className={`knowledge-status knowledge-status--${source.validation_status.toLowerCase()}`}>{sourceStatus(source)}</span><span className={`knowledge-status knowledge-status--coverage-${source.coverage_state.toLowerCase()}`}>{coverageStatus(source)}</span></div></div>
              <dl><div><dt>Current docs</dt><dd>{source.current_document_count}</dd></div><div><dt>Chunks</dt><dd>{source.chunk_count}</dd></div><div><dt>Ingestion</dt><dd>{source.ingestion_state === 'INGESTED' ? 'Ready' : 'Pending'}</dd></div><div><dt>Failed items</dt><dd>{source.failed_resource_count}</dd></div></dl>
              <p className="knowledge-base-source-card__time">Last successful check: {formatTime(source.last_successful_check_at)}</p>
              <p className="knowledge-base-source-card__time">Last ingestion: {formatTime(source.last_successful_ingestion_at)}</p>
              {source.latest_check && <p className="knowledge-base-source-card__time">Latest run: {source.latest_check.checked_documents} checked · {source.latest_check.changed_documents} changed</p>}
              <div className="knowledge-base-source-card__coverage"><strong>Covered categories</strong><p>{source.covered_categories.length ? source.covered_categories.map(readableCategory).join(' · ') : 'No current target category has verified evidence yet.'}</p><strong>Still missing</strong><p>{source.missing_categories.length ? source.missing_categories.map(readableCategory).join(' · ') : 'None'}</p></div>
              <div className="knowledge-base-source-card__links">
                {Array.from(new Map(source.entry_urls.map(url => [safeHostname(url), url])).entries()).map(([hostname, url]) => (
                  <a href={url} key={hostname} rel="noreferrer" target="_blank"><span>{hostname}</span><ExternalLink size={14} /></a>
                ))}
              </div>
            </article>
          ))}
        </div>
        {knowledgeBase.sources.length > 6 && !showAllSources && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
            <button className="secondary-action" onClick={() => setShowAllSources(true)} type="button">
              Show all {knowledgeBase.sources.length} sources
            </button>
          </div>
        )}
      </section>

      <section className="knowledge-base-section" aria-labelledby="recent-documents-title">
        <div className="knowledge-base-section__header"><div><p className="section-kicker">Extracted official documents</p><h2 id="recent-documents-title">Recently checked document versions</h2></div><span>{visibleDocuments.length} of {knowledgeBase.recent_documents.length} shown</span></div>
        <div className="knowledge-base-document-table-wrap">
          <table className="knowledge-base-document-table">
            <thead><tr><th>Source</th><th>Document</th><th>Status</th><th>Extraction</th><th>Last checked</th></tr></thead>
            <tbody>{visibleDocuments.map((document) => (
              <tr key={`${document.url}-${document.version_number}`}>
                <td>{document.source_name}</td>
                <td><a href={document.url} rel="noreferrer" target="_blank">{document.title}<ExternalLink size={13} /></a><small>Version {document.version_number}</small></td>
                <td><span className={`knowledge-status knowledge-status--${document.status.toLowerCase()}`}>{document.status}</span></td>
                <td>{document.extraction_method ?? 'Not recorded'}{document.is_ocr ? ' · OCR' : ''}</td>
                <td>{formatTime(document.last_checked_at)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        {knowledgeBase.recent_documents.length > 10 && !showAllDocuments && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1rem' }}>
            <button className="secondary-action" onClick={() => setShowAllDocuments(true)} type="button">
              Show all {knowledgeBase.recent_documents.length} documents
            </button>
          </div>
        )}
      </section>
      <p className="knowledge-base-page__privacy-note">For safety, this page does not expose document text, embeddings, file hashes, database details, API keys, or member information.</p>
    </main>
  )
}
