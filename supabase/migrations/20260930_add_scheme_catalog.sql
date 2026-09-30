-- Canonical, source-derived scheme catalogue.  Structured scheme records live
-- in PostgreSQL; Qdrant remains the derived semantic index for source chunks.
create table if not exists public.sahayak_schemes (
  id varchar(36) primary key,
  slug varchar(180) not null unique,
  normalized_name varchar(500) not null unique,
  official_name varchar(500) not null,
  short_name varchar(160),
  aliases jsonb not null default '[]'::jsonb,
  scheme_type varchar(48) not null,
  category varchar(96) not null,
  ministry varchar(240),
  implementing_authority varchar(240),
  geographic_scope varchar(32) not null default 'NATIONAL',
  applicable_states jsonb not null default '[]'::jsonb,
  applicable_districts jsonb not null default '[]'::jsonb,
  beneficiary_categories jsonb not null default '[]'::jsonb,
  relevant_user_types jsonb not null default '[]'::jsonb,
  status varchar(32) not null default 'UNKNOWN',
  verification_status varchar(32) not null default 'REVIEW_REQUIRED',
  current_version_number integer,
  first_discovered_at timestamptz not null,
  last_checked_at timestamptz not null,
  last_changed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists sahayak_schemes_status_idx
  on public.sahayak_schemes (status, verification_status);
create index if not exists sahayak_schemes_category_idx on public.sahayak_schemes (category);

create table if not exists public.sahayak_scheme_versions (
  id varchar(36) primary key,
  scheme_id varchar(36) not null references public.sahayak_schemes(id) on delete cascade,
  version_number integer not null,
  content_hash varchar(64) not null,
  status varchar(32) not null default 'UNKNOWN',
  verification_status varchar(32) not null default 'REVIEW_REQUIRED',
  data jsonb not null default '{}'::jsonb,
  evidence_summary text not null,
  publication_at timestamptz,
  effective_at timestamptz,
  expires_at timestamptz,
  first_retrieved_at timestamptz not null,
  last_checked_at timestamptz not null,
  last_changed_at timestamptz,
  is_current boolean not null default true,
  created_at timestamptz not null default now(),
  unique(scheme_id, version_number)
);

create index if not exists sahayak_scheme_versions_current_idx
  on public.sahayak_scheme_versions (is_current, status);
create index if not exists sahayak_scheme_versions_hash_idx
  on public.sahayak_scheme_versions (content_hash);

create table if not exists public.sahayak_scheme_sources (
  id varchar(36) primary key,
  scheme_version_id varchar(36) not null references public.sahayak_scheme_versions(id) on delete cascade,
  source_key varchar(96) not null references public.sahayak_knowledge_sources(key) on delete restrict,
  document_version_id varchar(36) not null references public.sahayak_knowledge_document_versions(id) on delete restrict,
  chunk_id varchar(36) references public.sahayak_knowledge_chunks(id) on delete set null,
  source_name varchar(200) not null,
  document_title varchar(500) not null,
  source_url text not null,
  relevant_section varchar(500),
  page_number integer,
  created_at timestamptz not null default now(),
  unique(scheme_version_id, document_version_id, chunk_id)
);

create index if not exists sahayak_scheme_sources_scheme_version_idx
  on public.sahayak_scheme_sources (scheme_version_id);
