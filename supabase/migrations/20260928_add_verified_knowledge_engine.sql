-- Sahayak AI verified-knowledge engine.
-- FastAPI and the scheduled worker are the only callers. Browser roles are
-- explicitly denied access to both source provenance and source content.

create table if not exists public.sahayak_knowledge_sources (
  key varchar(96) primary key,
  name varchar(200) not null,
  category varchar(96) not null,
  authority_level integer not null check (authority_level between 0 and 100),
  geographic_scope varchar(32) not null,
  check_interval_hours integer not null check (check_interval_hours > 0),
  approved_domains jsonb not null,
  entry_urls jsonb not null,
  discovery_path_prefixes jsonb not null default '[]'::jsonb,
  max_documents_per_check integer not null default 25 check (max_documents_per_check between 1 and 100),
  enabled boolean not null default true,
  validation_status varchar(32) not null default 'APPROVED' check (
    validation_status in ('APPROVED', 'DISABLED', 'CHECK_FAILED', 'REVIEW_REQUIRED')
  ),
  last_successful_check_at timestamptz,
  last_detected_change_at timestamptz,
  last_successful_ingestion_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Keep this migration safe for an environment where the source table was
-- provisioned from an earlier revision before discovery adapters existed.
alter table public.sahayak_knowledge_sources
  add column if not exists discovery_path_prefixes jsonb not null default '[]'::jsonb;
alter table public.sahayak_knowledge_sources
  add column if not exists max_documents_per_check integer not null default 25;

create table if not exists public.sahayak_knowledge_documents (
  id varchar(36) primary key,
  source_key varchar(96) not null references public.sahayak_knowledge_sources(key) on delete restrict,
  canonical_url text not null,
  title varchar(500) not null,
  source_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_key, canonical_url)
);

create index if not exists sahayak_knowledge_documents_source_idx
  on public.sahayak_knowledge_documents (source_key);

create table if not exists public.sahayak_knowledge_document_versions (
  id varchar(36) primary key,
  document_id varchar(36) not null references public.sahayak_knowledge_documents(id) on delete cascade,
  version_number integer not null check (version_number > 0),
  source_url text not null,
  title varchar(500) not null,
  content_hash varchar(64) not null,
  status varchar(32) not null check (
    status in ('CURRENT', 'SUPERSEDED', 'EXPIRED', 'REVIEW_REQUIRED', 'UNKNOWN', 'FETCH_FAILED', 'EXTRACTION_FAILED')
  ),
  publication_at timestamptz,
  effective_at timestamptz,
  expires_at timestamptz,
  first_retrieved_at timestamptz not null,
  last_checked_at timestamptz not null,
  last_modified_at timestamptz,
  storage_reference text,
  extraction_method varchar(64),
  is_ocr boolean not null default false,
  ocr_confidence double precision,
  source_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (document_id, version_number)
);

create index if not exists sahayak_knowledge_document_versions_current_idx
  on public.sahayak_knowledge_document_versions (status, effective_at);
create index if not exists sahayak_knowledge_document_versions_hash_idx
  on public.sahayak_knowledge_document_versions (content_hash);

create table if not exists public.sahayak_knowledge_chunks (
  id varchar(36) primary key,
  document_version_id varchar(36) not null references public.sahayak_knowledge_document_versions(id) on delete cascade,
  ordinal integer not null check (ordinal >= 0),
  heading varchar(500),
  content text not null,
  content_hash varchar(64) not null,
  vector_point_id varchar(96) not null unique,
  page_number integer check (page_number is null or page_number >= 0),
  language varchar(24),
  state varchar(100),
  district varchar(120),
  scheme_key varchar(120),
  created_at timestamptz not null default now(),
  unique (document_version_id, ordinal)
);

create index if not exists sahayak_knowledge_chunks_hash_idx
  on public.sahayak_knowledge_chunks (content_hash);
create index if not exists sahayak_knowledge_chunks_language_idx
  on public.sahayak_knowledge_chunks (language);
create index if not exists sahayak_knowledge_chunks_state_idx
  on public.sahayak_knowledge_chunks (state);
create index if not exists sahayak_knowledge_chunks_district_idx
  on public.sahayak_knowledge_chunks (district);
create index if not exists sahayak_knowledge_chunks_scheme_key_idx
  on public.sahayak_knowledge_chunks (scheme_key);

create table if not exists public.sahayak_knowledge_source_checks (
  id varchar(36) primary key,
  source_key varchar(96) not null references public.sahayak_knowledge_sources(key) on delete cascade,
  started_at timestamptz not null,
  completed_at timestamptz,
  result varchar(32) not null check (result in ('UNCHANGED', 'CHANGED', 'PARTIAL_FAILURE', 'FAILED')),
  checked_documents integer not null default 0 check (checked_documents >= 0),
  changed_documents integer not null default 0 check (changed_documents >= 0),
  failure_code varchar(96),
  details jsonb not null default '{}'::jsonb
);

create index if not exists sahayak_knowledge_source_checks_source_started_idx
  on public.sahayak_knowledge_source_checks (source_key, started_at desc);
create unique index if not exists sahayak_knowledge_source_checks_one_open_per_source
  on public.sahayak_knowledge_source_checks (source_key)
  where completed_at is null;

drop trigger if exists sahayak_knowledge_sources_touch_updated_at on public.sahayak_knowledge_sources;
create trigger sahayak_knowledge_sources_touch_updated_at
before update on public.sahayak_knowledge_sources
for each row execute function public.sahayak_touch_updated_at();

drop trigger if exists sahayak_knowledge_documents_touch_updated_at on public.sahayak_knowledge_documents;
create trigger sahayak_knowledge_documents_touch_updated_at
before update on public.sahayak_knowledge_documents
for each row execute function public.sahayak_touch_updated_at();

revoke all on table public.sahayak_knowledge_sources from anon, authenticated;
revoke all on table public.sahayak_knowledge_documents from anon, authenticated;
revoke all on table public.sahayak_knowledge_document_versions from anon, authenticated;
revoke all on table public.sahayak_knowledge_chunks from anon, authenticated;
revoke all on table public.sahayak_knowledge_source_checks from anon, authenticated;
