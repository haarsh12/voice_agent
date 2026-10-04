/**
 * Optimized Schemes View with pagination, caching, and skeleton loading
 */

import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { BookOpenCheck, ChevronRight } from 'lucide-react'

import { getSchemeDetail, getSchemeFilters, getSchemes } from '../lib/api'
import { cache } from '../lib/cache'
import type { SahayakProfile, SchemeDetail, SchemeFilters, SchemeSummary, UserType } from '../types/api'
import { SchemeCardSkeleton } from './SkeletonLoader'

const USER_TYPE_LABELS: Record<UserType, string> = {
  cooperative_member: 'Cooperative member',
  farmer: 'Farmer',
  pacs_member: 'PACS member',
  cooperative_official: 'Cooperative official',
  rural_stakeholder: 'Rural stakeholder',
  other: 'Other rural stakeholder',
}

type SchemeCardProps = {
  scheme: SchemeSummary
  onOpen: (scheme: SchemeSummary) => void
}

function SchemeCard({ scheme, onOpen }: SchemeCardProps) {
  return (
    <article className="scheme-card scheme-card--catalogue">
      <span><BookOpenCheck size={21} /></span>
      <p className="preview-badge">{scheme.category}</p>
      <h2>{scheme.official_name}</h2>
      <p>{scheme.description || 'Verified information is available in Sahayak AI.'}</p>
      <dl>
        <div>
          <dt>For</dt>
          <dd>
            {scheme.beneficiary_categories.length
              ? scheme.beneficiary_categories
                  .map((item) => USER_TYPE_LABELS[item as UserType] ?? item.replaceAll('_', ' '))
                  .join(', ')
              : 'See verified details'}
          </dd>
        </div>
        <div>
          <dt>Coverage</dt>
          <dd>
            {scheme.applicable_states.length
              ? scheme.applicable_states.join(', ')
              : scheme.geographic_scope === 'STATE'
                ? 'State-specific'
                : 'National / source-defined'}
          </dd>
        </div>
        <div>
          <dt>Current status</dt>
          <dd>
            {scheme.status === 'UNKNOWN'
              ? 'Current operational status not verified'
              : scheme.status.replaceAll('_', ' ')}
          </dd>
        </div>
      </dl>
      <button className="link-action" onClick={() => onOpen(scheme)} type="button">
        View details <ChevronRight size={15} />
      </button>
    </article>
  )
}

export function SchemesViewOptimized({
  onTalk,
  profile,
}: {
  onTalk: () => void
  profile?: SahayakProfile | null
}) {
  const isGuest = !profile
  const [guestAudience, setGuestAudience] = useState<string>('')
  const [category, setCategory] = useState('')
  const [state, setState] = useState('')
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [filters, setFilters] = useState<SchemeFilters>({
    categories: [],
    beneficiaries: [],
    states: [],
    types: [],
  })
  const [schemes, setSchemes] = useState<SchemeSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<SchemeDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [offset, setOffset] = useState(0)

  const loadSchemes = useCallback(
    async (loadMore = false) => {
      if (loadMore) {
        setLoadingMore(true)
      } else {
        setLoading(true)
        setOffset(0)
      }
      setError(null)

      const currentOffset = loadMore ? offset : 0

      try {
        const response = await getSchemes({
          query: submittedQuery,
          category: category || undefined,
          beneficiary: isGuest ? guestAudience || undefined : undefined,
          state: isGuest ? state || undefined : undefined,
          relevantToMe: !isGuest,
          offset: currentOffset,
          useCache: !loadMore && currentOffset === 0, // Use cache only for first page
        })

        if (loadMore) {
          setSchemes((prev) => [...prev, ...response.items])
          setOffset(currentOffset + response.items.length)
        } else {
          setSchemes(response.items)
          setOffset(response.items.length)
        }
        setTotal(response.total)
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : 'We could not load the verified scheme directory.'
        )
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    },
    [category, guestAudience, isGuest, state, submittedQuery, offset]
  )

  useEffect(() => {
    void getSchemeFilters()
      .then(setFilters)
      .catch(() => setFilters({ categories: [], beneficiaries: [], states: [], types: [] }))
  }, [])

  useEffect(() => {
    void loadSchemes(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, guestAudience, isGuest, state, submittedQuery])

  async function openScheme(scheme: SchemeSummary): Promise<void> {
    setDetailLoading(true)
    setSelected(null)
    try {
      setSelected(await getSchemeDetail(scheme.slug))
    } catch (detailError) {
      setError(
        detailError instanceof Error
          ? detailError.message
          : 'We could not open that scheme record.'
      )
    } finally {
      setDetailLoading(false)
    }
  }

  function clearCacheAndReload(): void {
    cache.clear()
    void loadSchemes(false)
  }

  const hasMore = offset < total
  const audienceLabel = profile?.user_type ? USER_TYPE_LABELS[profile.user_type] : 'your profile'

  return (
    <main className="portal-page">
      <header className="page-title">
        <p className="section-kicker">Scheme discovery</p>
        <h1>
          {isGuest ? 'Find verified support for your situation.' : 'Your relevant verified schemes.'}
        </h1>
        <p>
          {isGuest
            ? "Browse schemes, programmes and services discovered from Sahayak's connected official sources. Choose your category or location to narrow the directory."
            : `This directory is filtered using your Sahayak profile: ${audienceLabel}.`}
        </p>
      </header>

      <section className="scheme-toolbar" aria-label="Scheme audience">
        <div>
          <BookOpenCheck size={19} />
          <div>
            <strong>{isGuest ? 'Guest scheme directory' : 'Personalised scheme directory'}</strong>
            <p>
              {isGuest
                ? 'All currently verified records are available to browse. Tell Sahayak your category, state, crop or cooperative role for a focused shortlist.'
                : 'Your category and location are used only to surface potentially relevant records; they never guarantee eligibility.'}
            </p>
          </div>
        </div>
        <button className="link-action" onClick={clearCacheAndReload} type="button">
          Clear cache & reload
        </button>
      </section>

      <form
        className="scheme-filters"
        onSubmit={(event: FormEvent) => {
          event.preventDefault()
          setSubmittedQuery(query)
        }}
      >
        <input
          aria-label="Search verified schemes"
          maxLength={240}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search support, insurance, credit or a scheme name"
          value={query}
        />
        <select
          aria-label="Scheme category"
          onChange={(event) => setCategory(event.target.value)}
          value={category}
        >
          <option value="">All categories</option>
          {filters.categories.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        {isGuest && (
          <select
            aria-label="Your category"
            onChange={(event) => setGuestAudience(event.target.value)}
            value={guestAudience}
          >
            <option value="">All beneficiary groups</option>
            {filters.beneficiaries.map((item) => (
              <option key={item} value={item}>
                {USER_TYPE_LABELS[item as UserType] ?? item.replaceAll('_', ' ')}
              </option>
            ))}
          </select>
        )}
        {isGuest && (
          <select
            aria-label="State"
            onChange={(event) => setState(event.target.value)}
            value={state}
          >
            <option value="">All locations</option>
            {filters.states.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        )}
        <button className="secondary-action" type="submit">
          Search
        </button>
      </form>

      <p className="scheme-result-count" aria-live="polite">
        {loading
          ? 'Loading verified records…'
          : `${total} verified record${total === 1 ? '' : 's'} found · Showing ${schemes.length}`}
      </p>

      {error && <p className="inline-notice">{error}</p>}

      {/* Initial loading state */}
      {loading && schemes.length === 0 && (
        <section className="scheme-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <SchemeCardSkeleton key={i} />
          ))}
        </section>
      )}

      {/* Loaded schemes */}
      {!loading && schemes.length > 0 && (
        <section className="scheme-grid">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} onOpen={openScheme} />
          ))}
        </section>
      )}

      {/* Loading more skeletons */}
      {loadingMore && (
        <section className="scheme-grid">
          {Array.from({ length: 3 }).map((_, i) => (
            <SchemeCardSkeleton key={`more-${i}`} />
          ))}
        </section>
      )}

      {/* Load more button */}
      {!loading && hasMore && !loadingMore && (
        <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0' }}>
          <button className="secondary-action" onClick={() => void loadSchemes(true)} type="button">
            Load more schemes
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && schemes.length === 0 && (
        <div className="empty-state">
          <BookOpenCheck size={28} />
          <p>
            No verified record matches these filters yet. Ask Sahayak to narrow your need by
            category, state, crop, cooperative role or support type.
          </p>
          <button className="secondary-action" onClick={onTalk} type="button">
            Ask Sahayak
          </button>
        </div>
      )}

      {detailLoading && <p className="inline-notice">Opening verified scheme details…</p>}

      {selected && <SchemeDetailPanel scheme={selected} onAsk={onTalk} onClose={() => setSelected(null)} />}
    </main>
  )
}

function SchemeDetailPanel({
  scheme,
  onAsk,
  onClose,
}: {
  scheme: SchemeDetail
  onAsk: () => void
  onClose: () => void
}) {
  const dataValue = (key: string) =>
    typeof scheme.data[key] === 'string' ? (scheme.data[key] as string) : null
  const fields = [
    ['What this is', dataValue('description')],
    ['Objective', dataValue('objective')],
    ['Who it may fit', dataValue('eligibility')],
    ['What it provides', dataValue('benefits')],
    ['Documents', dataValue('required_documents')],
    ['How to apply', dataValue('application_process')],
    ['Important dates', dataValue('important_dates')],
  ].filter((item): item is [string, string] => Boolean(item[1]))

  return (
    <section className="scheme-detail-panel" aria-label="Verified scheme details">
      <div className="scheme-detail-panel__head">
        <div>
          <p className="section-kicker">{scheme.scheme_type.replaceAll('_', ' ')}</p>
          <h2>{scheme.official_name}</h2>
          <p>
            Potential relevance is based on recorded source information. It is not an eligibility
            guarantee.
          </p>
        </div>
        <button
          className="header-icon-button"
          onClick={onClose}
          type="button"
          aria-label="Close details"
        >
          ×
        </button>
      </div>
      <div className="scheme-detail-panel__content">
        {fields.length ? (
          fields.map(([label, value]) => (
            <article key={label}>
              <h3>{label}</h3>
              <p>{value}</p>
            </article>
          ))
        ) : (
          <p>Detailed fields have not yet been verified from the connected official record.</p>
        )}
      </div>
      <section className="scheme-detail-panel__sources">
        <h3>Verified information</h3>
        <p>
          These source records support the information shown in Sahayak AI. You can ask Sahayak to
          explain any part here.
        </p>
        <ul>
          {scheme.sources.map((source) => (
            <li key={`${source.source_name}-${source.title}-${source.relevant_section}`}>
              <strong>{source.source_name}</strong>
              <span>
                {source.title}
                {source.relevant_section ? ` · ${source.relevant_section}` : ''}
              </span>
            </li>
          ))}
        </ul>
      </section>
      <button className="primary-action" onClick={onAsk} type="button">
        Ask Sahayak about this
      </button>
    </section>
  )
}
