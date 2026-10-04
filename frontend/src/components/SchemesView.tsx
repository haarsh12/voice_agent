/**
 * SchemesView — Full-featured paginated scheme catalogue
 *
 * Design:
 * - First load shows 12 skeleton cards, then renders real data
 * - "Load more" / infinite-scroll pagination (no page flicker)
 * - Static SCHEMES_CATALOGUE provides instant offline fallback and seeds the
 *   card when the API doesn't yet have structured data for a scheme
 * - Scheme detail modal shows every structured field + official link
 * - Guest: sees all schemes with category / beneficiary / state filters
 * - Authenticated: sees schemes filtered by profile user_type automatically
 * - All scheme data is cached (3 min) so repeat visits are instant
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  BookOpenCheck,
  Building2,
  ChevronRight,
  ExternalLink,
  Filter,
  Landmark,
  MapPin,
  Phone,
  RefreshCw,
  Search,
  Tag,
  Users,
  X,
} from 'lucide-react'

import { getSchemeDetail, getSchemeFilters, getSchemes } from '../lib/api'
import {
  BENEFICIARY_TAGS,
  SCHEME_CATEGORIES,
  SCHEMES_CATALOGUE,
  getSchemeBySlug,
  type SchemeEntry,
} from '../data/schemes-catalogue'
import { SchemeCardSkeleton } from './SkeletonLoader'
import type { SahayakProfile, SchemeDetail, SchemeFilters, SchemeSummary, UserType } from '../types/api'

// ─── Constants ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 12

const USER_TYPE_LABELS: Record<UserType, string> = {
  cooperative_member: 'Cooperative member',
  farmer: 'Farmer',
  pacs_member: 'PACS member',
  cooperative_official: 'Cooperative official',
  rural_stakeholder: 'Rural stakeholder',
  other: 'Other rural stakeholder',
}

const SCHEME_TYPE_COLORS: Record<string, string> = {
  SCHEME: '#1a7340',
  INITIATIVE: '#1565c0',
  SERVICE: '#6a1b9a',
  POLICY: '#bf360c',
  PROGRAMME: '#00695c',
  FUND: '#e65100',
  INSURANCE: '#4527a0',
  FINANCIAL_PRODUCT: '#2e7d32',
}

// ─── Types ────────────────────────────────────────────────────────────────────

type DetailState =
  | { kind: 'idle' }
  | { kind: 'loading'; slug: string }
  | { kind: 'ready'; detail: SchemeDetail; local?: SchemeEntry }
  | { kind: 'error'; message: string }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function schemeTypeBadge(type: string) {
  const color = SCHEME_TYPE_COLORS[type] ?? '#555'
  return (
    <span
      className="scheme-type-badge"
      style={{ '--badge-color': color } as React.CSSProperties}
    >
      {type.replace(/_/g, ' ')}
    </span>
  )
}

function beneficiaryPills(tags: string[]) {
  return (
    <div className="scheme-beneficiary-pills">
      {tags.slice(0, 4).map((tag) => (
        <span key={tag} className="scheme-beneficiary-pill">
          {tag}
        </span>
      ))}
      {tags.length > 4 && (
        <span className="scheme-beneficiary-pill scheme-beneficiary-pill--more">
          +{tags.length - 4}
        </span>
      )}
    </div>
  )
}

// ─── Scheme Card ─────────────────────────────────────────────────────────────

function SchemeCard({
  summary,
  local,
  onOpen,
}: {
  summary: SchemeSummary
  local: SchemeEntry | undefined
  onOpen: () => void
}) {
  const description = summary.description || local?.description || 'Verified information is available in Sahayak AI.'
  const beneficiaries =
    local?.beneficiary_tags ??
    summary.beneficiary_categories.map((b) => USER_TYPE_LABELS[b as UserType] ?? b.replace(/_/g, ' '))
  const coverage =
    summary.applicable_states.length > 0
      ? summary.applicable_states.join(', ')
      : summary.geographic_scope === 'STATE'
        ? 'State-specific'
        : 'All India'
  const ministry = local?.ministry ?? ''

  return (
    <article className="scheme-card-v2" onClick={onOpen} onKeyDown={(e) => e.key === 'Enter' && onOpen()} tabIndex={0} role="button" aria-label={`View details for ${summary.official_name}`}>
      {/* Header */}
      <div className="scheme-card-v2__header">
        <div className="scheme-card-v2__icon">
          <BookOpenCheck size={18} />
        </div>
        <span className="scheme-card-v2__category">{summary.category}</span>
        {schemeTypeBadge(summary.scheme_type)}
      </div>

      {/* Title */}
      <h3 className="scheme-card-v2__title">{summary.official_name}</h3>
      {summary.short_name && summary.short_name !== summary.official_name && (
        <p className="scheme-card-v2__short-name">{summary.short_name}</p>
      )}

      {/* Description */}
      <p className="scheme-card-v2__desc">{description}</p>

      {/* Meta */}
      <dl className="scheme-card-v2__meta">
        {beneficiaries.length > 0 && (
          <div>
            <dt><Users size={11} /> Beneficiaries</dt>
            <dd>{beneficiaryPills(beneficiaries)}</dd>
          </div>
        )}
        <div>
          <dt><MapPin size={11} /> Coverage</dt>
          <dd>{coverage}</dd>
        </div>
        {ministry && (
          <div>
            <dt><Landmark size={11} /> Ministry</dt>
            <dd className="scheme-card-v2__ministry">{ministry}</dd>
          </div>
        )}
      </dl>

      {/* Footer */}
      <button className="scheme-card-v2__cta" type="button" onClick={(e) => { e.stopPropagation(); onOpen() }}>
        View details <ChevronRight size={14} />
      </button>
    </article>
  )
}

// ─── Detail Modal ─────────────────────────────────────────────────────────────

function SchemeDetailModal({
  detail,
  local,
  onClose,
  onAsk,
}: {
  detail: SchemeDetail
  local: SchemeEntry | undefined
  onClose: () => void
  onAsk: () => void
}) {
  const overlayRef = useRef<HTMLDivElement>(null)
  const d = (key: string): string | null =>
    typeof detail.data[key] === 'string' ? (detail.data[key] as string) : null

  // Merge API data with local catalogue entry
  const description = d('description') || local?.description || null
  const objective = d('objective') || local?.objective || null
  const benefits = d('benefits') || local?.benefits || null
  const eligibility = d('eligibility') || local?.eligibility || null
  const applicationProcess = d('application_process') || local?.application_process || null
  const requiredDocs = d('required_documents') || local?.required_documents || null
  const importantDates = d('important_dates') || null

  const officialUrl = local?.official_url ?? detail.sources[0]?.url ?? null
  const helpline = local?.helpline ?? null
  const launchedYear = local?.launched_year ?? null
  const budgetOutlay = local?.budget_outlay ?? null
  const beneficiaryTags = local?.beneficiary_tags ?? detail.beneficiary_categories.map((b) => USER_TYPE_LABELS[b as UserType] ?? b.replace(/_/g, ' '))
  const coverage =
    detail.applicable_states.length > 0
      ? detail.applicable_states.join(', ')
      : 'All India'

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = ''
    }
  }, [onClose])

  function handleOverlayClick(e: React.MouseEvent) {
    if (e.target === overlayRef.current) onClose()
  }

  const fields: Array<[string, string | null]> = [
    ['Description', description],
    ['Objective', objective],
    ['Benefits', benefits],
    ['Eligibility', eligibility],
    ['How to Apply', applicationProcess],
    ['Required Documents', requiredDocs],
    ['Important Dates', importantDates],
  ].filter((item): item is [string, string] => Boolean(item[1]))

  return (
    <div className="scheme-modal-overlay" ref={overlayRef} onClick={handleOverlayClick} role="dialog" aria-modal="true" aria-label={`Details for ${detail.official_name}`}>
      <div className="scheme-modal">
        {/* Modal Header */}
        <div className="scheme-modal__header">
          <div className="scheme-modal__header-left">
            <div className="scheme-modal__icon"><BookOpenCheck size={20} /></div>
            <div>
              {schemeTypeBadge(detail.scheme_type)}
              <span className="scheme-modal__category">{detail.category}</span>
              {local?.subcategory && <span className="scheme-modal__subcategory"> · {local.subcategory}</span>}
            </div>
          </div>
          <button className="scheme-modal__close" onClick={onClose} type="button" aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="scheme-modal__body">
          <h2 className="scheme-modal__title">{detail.official_name}</h2>
          {detail.short_name && detail.short_name !== detail.official_name && (
            <p className="scheme-modal__subtitle">{detail.short_name}</p>
          )}

          {/* Quick Info Strip */}
          <div className="scheme-modal__quick-info">
            {local?.ministry && (
              <div className="scheme-modal__info-chip">
                <Landmark size={13} />
                <span>{local.ministry}</span>
              </div>
            )}
            {local?.department && local.department !== local.ministry && (
              <div className="scheme-modal__info-chip">
                <Building2 size={13} />
                <span>{local.department}</span>
              </div>
            )}
            <div className="scheme-modal__info-chip">
              <MapPin size={13} />
              <span>{coverage}</span>
            </div>
            {launchedYear && (
              <div className="scheme-modal__info-chip">
                <Tag size={13} />
                <span>Launched {launchedYear}</span>
              </div>
            )}
            {budgetOutlay && (
              <div className="scheme-modal__info-chip">
                <Tag size={13} />
                <span>Outlay: {budgetOutlay}</span>
              </div>
            )}
          </div>

          {/* Beneficiaries */}
          {beneficiaryTags.length > 0 && (
            <section className="scheme-modal__section">
              <h3><Users size={14} /> Who Can Benefit?</h3>
              <div className="scheme-modal__beneficiaries">
                {beneficiaryTags.map((tag) => (
                  <span key={tag} className="scheme-modal__beneficiary-tag">{tag}</span>
                ))}
              </div>
            </section>
          )}

          {/* Detail Fields */}
          {fields.length > 0 ? (
            <div className="scheme-modal__fields">
              {fields.map(([label, value]) => (
                <section key={label} className="scheme-modal__field">
                  <h3>{label}</h3>
                  <p>{value}</p>
                </section>
              ))}
            </div>
          ) : (
            <p className="scheme-modal__no-data">
              Detailed fields are being verified from official sources. Ask Sahayak for the latest information.
            </p>
          )}

          {/* Sources */}
          {detail.sources.length > 0 && (
            <section className="scheme-modal__section scheme-modal__sources">
              <h3>Verified Sources</h3>
              <ul>
                {detail.sources.map((src) => (
                  <li key={`${src.source_name}-${src.title}`}>
                    <strong>{src.source_name}</strong>
                    <span>{src.title}{src.relevant_section ? ` · ${src.relevant_section}` : ''}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* External Links */}
          <div className="scheme-modal__links">
            {officialUrl && (
              <a
                href={officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="scheme-modal__official-link"
              >
                <ExternalLink size={15} />
                Visit Official Portal
              </a>
            )}
            {helpline && (
              <div className="scheme-modal__helpline">
                <Phone size={13} />
                Helpline: <strong>{helpline}</strong>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="scheme-modal__footer">
          <p className="scheme-modal__disclaimer">
            Relevance is based on recorded source information. This is not an eligibility guarantee.
          </p>
          <button className="primary-action" onClick={onAsk} type="button">
            Ask Sahayak about this
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function SchemesView({
  onTalk,
  profile,
}: {
  onTalk: () => void
  profile?: SahayakProfile | null
}) {
  const isGuest = !profile

  // Filter state
  const [searchInput, setSearchInput] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedBeneficiary, setSelectedBeneficiary] = useState('')
  const [selectedState, setSelectedState] = useState('')

  // Data state
  const [apiFilters, setApiFilters] = useState<SchemeFilters>({ categories: [], beneficiaries: [], states: [], types: [] })
  const [schemes, setSchemes] = useState<SchemeSummary[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Detail state
  const [detailState, setDetailState] = useState<DetailState>({ kind: 'idle' })

  // Show filter panel on mobile
  const [showFilters, setShowFilters] = useState(false)

  // ── Load API Filters ──
  useEffect(() => {
    getSchemeFilters()
      .then(setApiFilters)
      .catch(() => {/* use static fallback */})
  }, [])

  // ── Build filter options (prefer API; fall back to static catalogue) ──
  const categoryOptions = useMemo(
    () => (apiFilters.categories.length > 0 ? apiFilters.categories : SCHEME_CATEGORIES),
    [apiFilters.categories],
  )
  const beneficiaryOptions = useMemo(
    () => (apiFilters.beneficiaries.length > 0 ? apiFilters.beneficiaries : BENEFICIARY_TAGS),
    [apiFilters.beneficiaries],
  )

  // ── Load Schemes ──
  const loadSchemes = useCallback(
    async (isMore = false) => {
      const currentOffset = isMore ? offset : 0
      if (isMore) setIsLoadingMore(true)
      else { setIsLoading(true); setError(null) }

      try {
        const res = await getSchemes({
          query: submittedQuery,
          category: selectedCategory || undefined,
          beneficiary: isGuest ? selectedBeneficiary || undefined : undefined,
          state: isGuest ? selectedState || undefined : undefined,
          relevantToMe: !isGuest,
          offset: currentOffset,
          useCache: !isMore && currentOffset === 0,
        })

        if (isMore) {
          setSchemes((prev) => [...prev, ...res.items])
          setOffset(currentOffset + res.items.length)
        } else {
          setSchemes(res.items)
          setOffset(res.items.length)
        }
        setTotal(res.total)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Could not load schemes.'
        if (!isMore) setError(msg)
      } finally {
        setIsLoading(false)
        setIsLoadingMore(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [submittedQuery, selectedCategory, selectedBeneficiary, selectedState, isGuest],
  )

  // Initial + filter-change load
  useEffect(() => { void loadSchemes(false) }, [loadSchemes])

  // ── Open Detail ──
  async function openDetail(scheme: SchemeSummary) {
    const local = getSchemeBySlug(scheme.slug)
    setDetailState({ kind: 'loading', slug: scheme.slug })
    try {
      const detail = await getSchemeDetail(scheme.slug)
      setDetailState({ kind: 'ready', detail, local })
    } catch {
      // Graceful fallback: build a minimal SchemeDetail from local catalogue
      if (local) {
        const fallbackDetail: SchemeDetail = {
          id: scheme.id,
          slug: scheme.slug,
          official_name: local.official_name,
          short_name: local.short_name,
          scheme_type: local.scheme_type,
          category: local.category,
          description: local.description,
          beneficiary_categories: local.relevant_user_types,
          relevant_user_types: local.relevant_user_types,
          applicable_states: local.applicable_states,
          applicable_districts: [],
          geographic_scope: local.geographic_scope,
          status: local.status,
          verification_status: 'APPROVED',
          last_checked_at: new Date().toISOString(),
          data: {
            description: local.description,
            objective: local.objective,
            benefits: local.benefits,
            eligibility: local.eligibility,
            application_process: local.application_process,
            required_documents: local.required_documents,
          },
          sources: local.official_url
            ? [{ source_name: local.ministry, title: `${local.official_name} Official Portal`, url: local.official_url, relevant_section: null, page_number: null, document_version: null }]
            : [],
          current_version_number: null,
        }
        setDetailState({ kind: 'ready', detail: fallbackDetail, local })
      } else {
        setDetailState({ kind: 'error', message: 'Could not load scheme details.' })
      }
    }
  }

  const hasMore = offset < total
  const audienceLabel = profile?.user_type ? USER_TYPE_LABELS[profile.user_type] : 'your profile'
  const activeFiltersCount = [selectedCategory, selectedBeneficiary, selectedState].filter(Boolean).length

  return (
    <main className="portal-page schemes-page">
      {/* Page Header */}
      <header className="page-title schemes-page__header">
        <p className="section-kicker">Scheme Discovery</p>
        <h1>{isGuest ? 'Government Schemes & Programmes' : 'Your Relevant Schemes'}</h1>
        <p>
          {isGuest
            ? '45 verified government schemes, programmes and services — with full details, eligibility and official links.'
            : `Showing schemes relevant to ${audienceLabel}. All 45 schemes are always available via search.`}
        </p>
      </header>

      {/* Toolbar */}
      <section className="schemes-toolbar">
        {/* Search */}
        <form
          className="schemes-search"
          onSubmit={(e) => { e.preventDefault(); setSubmittedQuery(searchInput) }}
        >
          <div className="schemes-search__input-wrap">
            <Search size={16} className="schemes-search__icon" />
            <input
              aria-label="Search schemes"
              maxLength={240}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by scheme name, benefit, or keyword…"
              value={searchInput}
              className="schemes-search__input"
            />
            {searchInput && (
              <button
                type="button"
                className="schemes-search__clear"
                onClick={() => { setSearchInput(''); setSubmittedQuery('') }}
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button className="secondary-action schemes-search__btn" type="submit">Search</button>
        </form>

        {/* Filter toggle (mobile) */}
        <button
          className={`schemes-filter-toggle ${showFilters ? 'schemes-filter-toggle--active' : ''}`}
          type="button"
          onClick={() => setShowFilters((v) => !v)}
          aria-label="Toggle filters"
        >
          <Filter size={15} />
          Filters
          {activeFiltersCount > 0 && <span className="schemes-filter-toggle__count">{activeFiltersCount}</span>}
        </button>
      </section>

      {/* Filters Row */}
      <div className={`schemes-filters ${showFilters ? 'schemes-filters--open' : ''}`}>
        <select
          aria-label="Filter by category"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="schemes-filter-select"
        >
          <option value="">All categories</option>
          {categoryOptions.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        {isGuest && (
          <select
            aria-label="Filter by beneficiary"
            value={selectedBeneficiary}
            onChange={(e) => setSelectedBeneficiary(e.target.value)}
            className="schemes-filter-select"
          >
            <option value="">All beneficiary groups</option>
            {beneficiaryOptions.map((b) => (
              <option key={b} value={b}>
                {USER_TYPE_LABELS[b as UserType] ?? b.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        )}

        {isGuest && (
          <select
            aria-label="Filter by state"
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="schemes-filter-select"
          >
            <option value="">All locations</option>
            {apiFilters.states.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        )}

        {activeFiltersCount > 0 && (
          <button
            className="link-action schemes-clear-filters"
            type="button"
            onClick={() => { setSelectedCategory(''); setSelectedBeneficiary(''); setSelectedState('') }}
          >
            <X size={13} /> Clear filters
          </button>
        )}
      </div>

      {/* Result Count */}
      <p className="schemes-result-count" aria-live="polite">
        {isLoading
          ? 'Loading schemes…'
          : `${total} scheme${total === 1 ? '' : 's'} found${schemes.length < total ? ` · showing ${schemes.length}` : ''}`}
        <button
          className="schemes-refresh"
          type="button"
          onClick={() => void loadSchemes(false)}
          aria-label="Refresh"
          title="Refresh"
        >
          <RefreshCw size={13} />
        </button>
      </p>

      {/* Error */}
      {error && <p className="inline-notice">{error}</p>}

      {/* Grid: initial skeleton */}
      {isLoading && schemes.length === 0 && (
        <section className="schemes-grid" aria-label="Loading schemes">
          {Array.from({ length: PAGE_SIZE }).map((_, i) => <SchemeCardSkeleton key={i} />)}
        </section>
      )}

      {/* Grid: loaded schemes */}
      {schemes.length > 0 && (
        <section className="schemes-grid">
          {schemes.map((scheme) => (
            <SchemeCard
              key={scheme.id}
              summary={scheme}
              local={getSchemeBySlug(scheme.slug)}
              onOpen={() => void openDetail(scheme)}
            />
          ))}
          {/* Load more skeletons */}
          {isLoadingMore && Array.from({ length: 3 }).map((_, i) => <SchemeCardSkeleton key={`more-${i}`} />)}
        </section>
      )}

      {/* Empty state */}
      {!isLoading && schemes.length === 0 && !error && (
        <div className="empty-state">
          <BookOpenCheck size={32} />
          <p>No schemes match these filters. Try a different keyword or clear the filters.</p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
            {activeFiltersCount > 0 && (
              <button className="secondary-action" type="button" onClick={() => { setSelectedCategory(''); setSelectedBeneficiary(''); setSelectedState('') }}>
                Clear filters
              </button>
            )}
            <button className="secondary-action" type="button" onClick={onTalk}>
              Ask Sahayak
            </button>
          </div>
        </div>
      )}

      {/* Load More */}
      {!isLoading && !isLoadingMore && hasMore && (
        <div className="schemes-load-more">
          <button
            className="secondary-action"
            type="button"
            onClick={() => void loadSchemes(true)}
          >
            Load more schemes
          </button>
          <span className="schemes-load-more__count">
            Showing {schemes.length} of {total}
          </span>
        </div>
      )}

      {/* Detail Modal */}
      {detailState.kind === 'loading' && (
        <div className="scheme-modal-overlay scheme-modal-overlay--loading" aria-live="polite">
          <div className="scheme-modal-spinner">
            <span className="loader-ring" />
            Loading scheme details…
          </div>
        </div>
      )}
      {detailState.kind === 'error' && (
        <p className="inline-notice">{detailState.message}</p>
      )}
      {detailState.kind === 'ready' && (
        <SchemeDetailModal
          detail={detailState.detail}
          local={detailState.local}
          onClose={() => setDetailState({ kind: 'idle' })}
          onAsk={() => { setDetailState({ kind: 'idle' }); onTalk() }}
        />
      )}
    </main>
  )
}
