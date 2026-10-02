-- Migration: Add performance indexes for knowledge retrieval optimization
-- Purpose: Significantly improve query performance for knowledge retrieval
-- Impact: Reduces retrieval latency from ~4.7s to <1.5s target
-- Safe to run: Creates indexes concurrently (CONCURRENT option for production)

-- ==================================================================
-- KNOWLEDGE CHUNKS INDEXES
-- ==================================================================

-- Composite index for vector point lookups with status filter
-- Used in: current_chunks_for_vector_points
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_vector_status 
ON sahayak_knowledge_chunks(vector_point_id, document_id) 
WHERE vector_point_id IS NOT NULL;

-- Composite index for geographic filtering with status
-- Used in: state/district filtering during retrieval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_geography 
ON sahayak_knowledge_chunks(state, district, document_id) 
WHERE state IS NOT NULL OR district IS NOT NULL;

-- Full-text search optimization for lexical fallback
-- Used in: current_chunks_for_text_search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_content_text 
ON sahayak_knowledge_chunks USING gin(to_tsvector('english', content));

-- Language filtering for multilingual support
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chunks_language 
ON sahayak_knowledge_chunks(language, document_id) 
WHERE language IS NOT NULL;

-- ==================================================================
-- KNOWLEDGE DOCUMENTS INDEXES
-- ==================================================================

-- Composite index for source + status lookups
-- Used in: document version validation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_source_status 
ON sahayak_knowledge_documents(source_key, status, version_number);

-- Index for expiration checks
-- Used in: filtering expired documents
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_expiration 
ON sahayak_knowledge_documents(expires_at, status) 
WHERE expires_at IS NOT NULL;

-- Publication date for freshness sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_publication 
ON sahayak_knowledge_documents(publication_at DESC, source_key);

-- ==================================================================
-- KNOWLEDGE SOURCES INDEXES
-- ==================================================================

-- Authority level for evidence ranking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sources_authority 
ON sahayak_knowledge_sources(authority_level DESC, key);

-- Last checked timestamp for ingestion scheduling
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sources_last_checked 
ON sahayak_knowledge_sources(last_checked_at NULLS FIRST);

-- ==================================================================
-- SCHEMES INDEXES (for catalog search)
-- ==================================================================

-- Full-text search on scheme names and descriptions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_search 
ON sahayak_schemes USING gin(
    to_tsvector('english', 
        COALESCE(official_name, '') || ' ' || 
        COALESCE(common_name, '') || ' ' || 
        COALESCE(description, '')
    )
);

-- Scheme category and type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_category_type 
ON sahayak_schemes(category, scheme_type, is_active);

-- Geographic scope filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_schemes_geography 
ON sahayak_schemes(state, is_active) 
WHERE state IS NOT NULL;

-- ==================================================================
-- ACCOUNT & AUTH INDEXES (if not already present)
-- ==================================================================

-- Email lookup for authentication (if not exists)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_email 
ON sahayak_accounts(email) 
WHERE email IS NOT NULL;

-- Phone lookup for OTP auth
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_phone 
ON sahayak_accounts(phone_number) 
WHERE phone_number IS NOT NULL;

-- Active accounts filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_active 
ON sahayak_accounts(is_active, created_at DESC);

-- ==================================================================
-- STATISTICS UPDATE
-- ==================================================================

-- Update table statistics for query planner
ANALYZE sahayak_knowledge_chunks;
ANALYZE sahayak_knowledge_documents;
ANALYZE sahayak_knowledge_sources;
ANALYZE sahayak_schemes;
ANALYZE sahayak_accounts;

-- ==================================================================
-- VERIFICATION QUERIES
-- ==================================================================

-- Run these to verify indexes were created successfully:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename LIKE 'sahayak_%' ORDER BY tablename, indexname;
-- SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE tablename LIKE 'sahayak_%' ORDER BY tablename;
