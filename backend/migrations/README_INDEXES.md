# Database Performance Indexes

## Purpose
These indexes significantly improve knowledge retrieval performance by optimizing the most common query patterns in the Sahayak voice agent.

## Expected Impact
- **Before**: ~4.7s knowledge retrieval latency
- **After**: <1.5s target latency (70%+ improvement)
- **Cache hit rate**: 60-80% after warm-up

## How to Apply

### Development (SQLite)
SQLite doesn't support `CONCURRENTLY`, so use the non-concurrent version:

```bash
# From backend directory
python -c "
from app.auth.session import get_engine
import asyncio

async def apply_indexes():
    engine = get_engine()
    async with engine.begin() as conn:
        # Read and execute SQL (remove CONCURRENTLY keyword for SQLite)
        with open('migrations/add_performance_indexes.sql') as f:
            sql = f.read().replace('CONCURRENTLY ', '')
            # Execute each statement separately
            for statement in sql.split(';'):
                if statement.strip() and not statement.strip().startswith('--'):
                    await conn.execute(statement)
    print('Indexes applied successfully')

asyncio.run(apply_indexes())
"
```

### Production (PostgreSQL/Supabase)
Use the CONCURRENTLY option to avoid table locks:

```bash
# Connect to your database
psql $DATABASE_URL

# Or for Supabase
psql "postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres"

# Run the migration
\i migrations/add_performance_indexes.sql
```

### Using Alembic (Recommended for Production)
If using Alembic migrations:

```bash
# Generate migration
alembic revision -m "add_performance_indexes"

# Edit the generated file to include the SQL
# Then apply
alembic upgrade head
```

## Verification

Check that indexes were created:

```sql
-- List all Sahayak indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename LIKE 'sahayak_%' 
ORDER BY tablename, indexname;

-- Check index usage (after running for a while)
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE 'sahayak_%'
ORDER BY idx_scan DESC;
```

## Index Descriptions

### Critical for Performance
1. **idx_chunks_vector_status**: Speeds up vector point → chunk lookups (most common query)
2. **idx_chunks_content_text**: GIN index for lexical fallback search
3. **idx_documents_source_status**: Fast document validation

### Geographic Filtering
4. **idx_chunks_geography**: State/district filtering for localized results
5. **idx_schemes_geography**: Scheme geographic scope

### Full-Text Search
6. **idx_chunks_content_text**: Content search with PostgreSQL FTS
7. **idx_schemes_search**: Scheme name and description search

### Ranking & Sorting
8. **idx_sources_authority**: Evidence prioritization by source authority
9. **idx_documents_publication**: Freshness-based sorting

## Maintenance

### Rebuild if needed
```sql
-- Reindex specific index
REINDEX INDEX CONCURRENTLY idx_chunks_vector_status;

-- Reindex entire table
REINDEX TABLE CONCURRENTLY sahayak_knowledge_chunks;
```

### Monitor size
```sql
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE tablename LIKE 'sahayak_%'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

## Rollback

If you need to remove these indexes:

```sql
-- Drop indexes (be careful in production!)
DROP INDEX CONCURRENTLY IF EXISTS idx_chunks_vector_status;
DROP INDEX CONCURRENTLY IF EXISTS idx_chunks_geography;
DROP INDEX CONCURRENTLY IF EXISTS idx_chunks_content_text;
DROP INDEX CONCURRENTLY IF EXISTS idx_chunks_language;
DROP INDEX CONCURRENTLY IF EXISTS idx_documents_source_status;
DROP INDEX CONCURRENTLY IF EXISTS idx_documents_expiration;
DROP INDEX CONCURRENTLY IF EXISTS idx_documents_publication;
DROP INDEX CONCURRENTLY IF EXISTS idx_sources_authority;
DROP INDEX CONCURRENTLY IF EXISTS idx_sources_last_checked;
DROP INDEX CONCURRENTLY IF EXISTS idx_schemes_search;
DROP INDEX CONCURRENTLY IF EXISTS idx_schemes_category_type;
DROP INDEX CONCURRENTLY IF EXISTS idx_schemes_geography;
DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_email;
DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_phone;
DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_active;
```

## Notes
- `CONCURRENTLY` prevents table locks but takes longer to build
- Indexes increase write time slightly but dramatically improve read performance
- For voice agents with read-heavy workloads, this tradeoff is highly favorable
- Update statistics regularly with `ANALYZE` for optimal query planning
