/**
 * Skeleton loading components for better perceived performance
 */

import './SkeletonLoader.css'

export function SkeletonBox({ width = '100%', height = '1rem', className = '' }: { width?: string; height?: string; className?: string }) {
  return <div className={`skeleton-box ${className}`} style={{ width, height }} />
}

export function SkeletonText({ lines = 1, width = '100%' }: { lines?: number; width?: string }) {
  return (
    <div className="skeleton-text" style={{ width }}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBox key={i} height="0.875rem" width={i === lines - 1 ? '70%' : '100%'} />
      ))}
    </div>
  )
}

export function SchemeCardSkeleton() {
  return (
    <article className="scheme-card scheme-card--skeleton">
      <span className="scheme-card__icon-skeleton">
        <SkeletonBox width="21px" height="21px" />
      </span>
      <div className="scheme-card__badge-skeleton">
        <SkeletonBox width="80px" height="20px" />
      </div>
      <SkeletonBox height="1.5rem" width="85%" />
      <SkeletonText lines={2} />
      <div className="scheme-card__details-skeleton">
        <div>
          <SkeletonBox height="0.75rem" width="40px" />
          <SkeletonBox height="1rem" width="120px" />
        </div>
        <div>
          <SkeletonBox height="0.75rem" width="60px" />
          <SkeletonBox height="1rem" width="100px" />
        </div>
      </div>
      <SkeletonBox height="1rem" width="100px" />
    </article>
  )
}

export function KnowledgeSourceCardSkeleton() {
  return (
    <article className="knowledge-base-source-card knowledge-base-source-card--skeleton">
      <div className="knowledge-base-source-card__heading">
        <div>
          <SkeletonBox height="1.25rem" width="200px" />
          <SkeletonBox height="0.875rem" width="150px" />
        </div>
        <div className="knowledge-base-source-card__status-stack">
          <SkeletonBox width="80px" height="20px" />
          <SkeletonBox width="100px" height="20px" />
        </div>
      </div>
      <dl>
        <div>
          <dt><SkeletonBox width="60px" height="0.75rem" /></dt>
          <dd><SkeletonBox width="30px" height="1rem" /></dd>
        </div>
        <div>
          <dt><SkeletonBox width="50px" height="0.75rem" /></dt>
          <dd><SkeletonBox width="40px" height="1rem" /></dd>
        </div>
        <div>
          <dt><SkeletonBox width="60px" height="0.75rem" /></dt>
          <dd><SkeletonBox width="50px" height="1rem" /></dd>
        </div>
        <div>
          <dt><SkeletonBox width="70px" height="0.75rem" /></dt>
          <dd><SkeletonBox width="20px" height="1rem" /></dd>
        </div>
      </dl>
      <SkeletonText lines={1} />
      <SkeletonText lines={1} />
      <div className="knowledge-base-source-card__coverage">
        <SkeletonBox height="0.875rem" width="140px" />
        <SkeletonText lines={1} />
        <SkeletonBox height="0.875rem" width="100px" />
        <SkeletonText lines={1} />
      </div>
    </article>
  )
}

export function MetricCardSkeleton() {
  return (
    <article className="metric-skeleton">
      <SkeletonBox width="20px" height="20px" />
      <SkeletonBox height="0.875rem" width="100px" />
      <SkeletonBox height="2rem" width="60px" />
      <SkeletonBox height="0.75rem" width="120px" />
    </article>
  )
}
