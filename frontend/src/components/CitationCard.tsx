import { ExternalLink, FileText, Calendar, CheckCircle, AlertTriangle } from 'lucide-react'
import type { OfficialSourceReference } from '../types/api'
import './CitationCard.css'

type CitationCardProps = {
  citation: OfficialSourceReference
  compact?: boolean
}

function freshnessStatusLabel(status: string): string {
  switch (status) {
    case 'CURRENT':
      return 'Current'
    case 'UPDATED':
      return 'Recently updated'
    case 'SUPERSEDED':
      return 'Superseded'
    case 'ARCHIVED':
      return 'Archived'
    default:
      return 'Unknown'
  }
}

function freshnessStatusIcon(status: string) {
  switch (status) {
    case 'CURRENT':
    case 'UPDATED':
      return <CheckCircle size={14} className="citation-card__status-icon citation-card__status-icon--current" />
    case 'SUPERSEDED':
    case 'ARCHIVED':
      return <AlertTriangle size={14} className="citation-card__status-icon citation-card__status-icon--warning" />
    default:
      return null
  }
}

function formatPublicationDate(dateString: string | undefined): string {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-IN', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch {
    return ''
  }
}

export function CitationCard({ citation, compact = false }: CitationCardProps) {
  const handleClick = (e: React.MouseEvent) => {
    // Let the browser handle the link naturally
    // Analytics or tracking could be added here
  }

  if (compact) {
    return (
      <div className="citation-card citation-card--compact">
        <FileText size={16} className="citation-card__icon" aria-hidden="true" />
        <div className="citation-card__content">
          <strong className="citation-card__source-name">{citation.name}</strong>
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="citation-card__link"
            onClick={handleClick}
            aria-label={`Open ${citation.title} in new tab`}
          >
            {citation.title}
            <ExternalLink size={14} className="citation-card__external-icon" aria-hidden="true" />
          </a>
        </div>
      </div>
    )
  }

  return (
    <article className="citation-card" role="article">
      <header className="citation-card__header">
        <FileText size={20} className="citation-card__icon" aria-hidden="true" />
        <div className="citation-card__header-content">
          <h4 className="citation-card__source-name">{citation.name}</h4>
          {citation.freshness_status && (
            <div className="citation-card__status">
              {freshnessStatusIcon(citation.freshness_status)}
              <span className="citation-card__status-label">
                {freshnessStatusLabel(citation.freshness_status)}
              </span>
            </div>
          )}
        </div>
      </header>

      <a
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="citation-card__link citation-card__link--primary"
        onClick={handleClick}
      >
        <span className="citation-card__title">{citation.title}</span>
        <ExternalLink size={16} className="citation-card__external-icon" aria-hidden="true" />
      </a>

      {citation.document_version && (
        <p className="citation-card__metadata">
          Version {citation.document_version}
        </p>
      )}

      {(citation.published_at || citation.effective_at) && (
        <footer className="citation-card__footer">
          {citation.published_at && (
            <div className="citation-card__date">
              <Calendar size={14} aria-hidden="true" />
              <span>Published: {formatPublicationDate(citation.published_at)}</span>
            </div>
          )}
          {citation.effective_at && citation.effective_at !== citation.published_at && (
            <div className="citation-card__date">
              <Calendar size={14} aria-hidden="true" />
              <span>Effective: {formatPublicationDate(citation.effective_at)}</span>
            </div>
          )}
        </footer>
      )}
    </article>
  )
}

type CitationListProps = {
  citations: OfficialSourceReference[]
  title?: string
  compact?: boolean
  className?: string
}

export function CitationList({ 
  citations, 
  title = '📚 Official Sources', 
  compact = false,
  className = ''
}: CitationListProps) {
  if (!citations || citations.length === 0) {
    return null
  }

  return (
    <section className={`citation-list ${className}`} aria-label="Official source citations">
      {title && <h3 className="citation-list__title">{title}</h3>}
      <div className={`citation-list__grid ${compact ? 'citation-list__grid--compact' : ''}`}>
        {citations.map((citation, index) => (
          <CitationCard 
            key={`${citation.url}-${index}`} 
            citation={citation} 
            compact={compact}
          />
        ))}
      </div>
    </section>
  )
}

type GeneralGuidanceNoticeProps = {
  className?: string
}

export function GeneralGuidanceNotice({ className = '' }: GeneralGuidanceNoticeProps) {
  return (
    <div className={`citation-notice citation-notice--general ${className}`} role="note">
      <AlertTriangle size={16} aria-hidden="true" />
      <span>General Guidance – Not from official verified sources</span>
    </div>
  )
}
