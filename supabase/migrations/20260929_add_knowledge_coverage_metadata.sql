-- Coverage is separate from source reachability and ingestion outcome.
-- A healthy source with one indexed document must remain visibly incomplete
-- until every reviewed product category has current evidence.

alter table public.sahayak_knowledge_sources
  add column if not exists expected_categories jsonb not null default '[]'::jsonb;

alter table public.sahayak_knowledge_document_versions
  add column if not exists coverage_categories jsonb not null default '[]'::jsonb;

create index if not exists sahayak_knowledge_document_versions_coverage_categories_idx
  on public.sahayak_knowledge_document_versions using gin (coverage_categories);

create table if not exists public.sahayak_knowledge_failed_resources (
  id varchar(36) primary key,
  source_key varchar(96) not null references public.sahayak_knowledge_sources(key) on delete cascade,
  canonical_url text not null,
  failure_code varchar(96) not null,
  first_failed_at timestamptz not null,
  last_failed_at timestamptz not null,
  retry_count integer not null default 1 check (retry_count >= 1),
  next_retry_at timestamptz not null,
  status varchar(24) not null default 'PENDING' check (status in ('PENDING', 'RESOLVED')),
  resolved_at timestamptz,
  unique (source_key, canonical_url)
);

create index if not exists sahayak_knowledge_failed_resources_retry_idx
  on public.sahayak_knowledge_failed_resources (source_key, next_retry_at);

revoke all on table public.sahayak_knowledge_failed_resources from anon, authenticated;
