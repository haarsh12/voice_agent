# Knowledge System Quick Reference Card

## Quick Start

### First Time Setup
```bash
# 1. Start required services
docker-compose up -d qdrant

# 2. Run bulk ingestion (30-60 min)
cd backend
ingest_all_sources.bat

# 3. Test everything
test_pipeline.bat
```

### Daily Use
```bash
# Check due sources (scheduled)
python -m app.knowledge.cli

# Test specific query
python -c "
from app.knowledge.retrieval import KnowledgeRetriever
from app.auth.session import get_session_factory
from app.config.settings import get_settings
import asyncio

async def test():
    async with get_session_factory()() as session:
        result = await KnowledgeRetriever(session, get_settings()).retrieve('PM-KISAN scheme')
        print(f'Evidence: {len(result.evidence)}, Citations: {len(result.citations)}')
asyncio.run(test())
"
```

## Common Commands

| Task | Command |
|------|---------|
| **Ingest all sources** | `python -m app.knowledge.cli --ingest-all` |
| **Ingest specific source** | `python -m app.knowledge.cli --source ncdc` |
| **Check due sources** | `python -m app.knowledge.cli` |
| **Backfill schemes** | `python -m app.knowledge.cli --backfill-schemes` |
| **Reconcile vectors** | `python -m app.knowledge.cli --reconcile` |
| **Reindex source** | `python -m app.knowledge.cli --reindex-source pm_kisan` |
| **Test pipeline** | `python test_knowledge_pipeline.py` |
| **List sources** | `curl http://localhost:8000/api/admin/knowledge/sources` |

## Important Sources

| Key | Name | Coverage |
|-----|------|----------|
| **ncdc** | NCDC | Yuva Sahakar, Sahakar Mitra, Dairy Sahakar |
| **pm_kisan** | PM-KISAN | Direct income support |
| **pmfby** | PMFBY | Crop insurance |
| **kisan_credit_card** | KCC | Agricultural credit |
| **agriculture_infrastructure_fund** | AIF | Infrastructure financing |
| **pmksy** | PMKSY | Irrigation |
| **ministry_of_fisheries** | Fisheries | PMMSY, FIDF |
| **department_animal_husbandry_dairying** | Livestock & Dairy | Gokul Mission, NLM |
| **food_processing_ministry** | Food Processing | PMFME, Sampada |
| **trifed** | TRIFED | Van Dhan Vikas |
| **maharashtra_agriculture** | Maharashtra Agri | State schemes |

## Database Quick Checks

```sql
-- Check ingestion status
SELECT source_key, COUNT(*) as docs 
FROM knowledge_documents 
GROUP BY source_key;

-- Check schemes by category
SELECT category, COUNT(*) 
FROM schemes 
GROUP BY category 
ORDER BY COUNT(*) DESC;

-- Recent ingestions
SELECT source_key, status, checked_at 
FROM knowledge_source_checks 
ORDER BY checked_at DESC 
LIMIT 10;

-- Failed documents
SELECT d.source_key, d.canonical_url, v.status 
FROM knowledge_documents d 
JOIN knowledge_document_versions v ON v.document_id = d.id 
WHERE v.status IN ('FETCH_FAILED', 'EXTRACTION_FAILED');
```

## Qdrant Checks

```bash
# Collection info
curl http://localhost:6333/collections/sahayak_knowledge

# Collection statistics
curl http://localhost:6333/collections/sahayak_knowledge | jq '.result.vectors_count'
```

## Test Queries for Voice Agent

### Hindi
- "मुझे युवा सहकार योजना के बारे में बताओ"
- "PM-KISAN के बारे में जानकारी दो"
- "NCDC से loan कैसे मिलता है?"
- "मत्स्य पालन के लिए क्या schemes हैं?"
- "Maharashtra में farmers के लिए schemes"

### English
- "Tell me about Yuva Sahakar scheme"
- "What is PM-KISAN?"
- "How to get NCDC loan?"
- "Fisheries schemes available"
- "Dairy development programs"

### Marathi
- "युवा सहकार योजनेबद्दल सांगा"
- "शेतकऱ्यांसाठी कोणत्या योजना आहेत?"
- "सहकारी कर्ज कसे मिळेल?"

## Expected Results

✓ Citations show with source URLs  
✓ URLs are clickable (*.gov.in)  
✓ Agent doesn't speak URLs  
✓ "General Guidance" when no official sources  
✓ Responses are concise (2-3 sentences)

## Troubleshooting Fast Track

| Problem | Quick Fix |
|---------|-----------|
| No documents | `python -m app.knowledge.cli --ingest-all` |
| No schemes | `python -m app.knowledge.cli --backfill-schemes` |
| No vectors | `python -m app.knowledge.cli --reconcile` |
| No citations | Check Qdrant is running, verify retrieval works |
| OCR fails | Set `GOOGLE_VISION_API_ENABLED=true` in .env |
| Network timeout | Retry during IST business hours |

## File Locations

| File | Purpose |
|------|---------|
| `app/knowledge/registry.py` | Source definitions (27 sources) |
| `app/schemes/extraction.py` | Scheme categorization logic |
| `app/agent/prompts.py` | Agent instructions for citations |
| `app/knowledge/cli.py` | Ingestion CLI tool |
| `app/admin/routes.py` | Admin API endpoints |
| `KNOWLEDGE_INGESTION_GUIDE.md` | Complete manual |
| `TESTING_KNOWLEDGE_PIPELINE.md` | Test procedures |
| `KNOWLEDGE_SYSTEM_SUMMARY.md` | System overview |

## Admin API Quick Reference

```bash
# Cookie auth required
SESSION="admin_session=YOUR_SESSION_COOKIE"

# Trigger ingestion (all due sources)
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" -d '{}' --cookie "$SESSION"

# Force ingest all sources
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" -d '{"force_all": true}' --cookie "$SESSION"

# Ingest specific source
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" -d '{"source_key": "ncdc"}' --cookie "$SESSION"

# List all sources
curl http://localhost:8000/api/admin/knowledge/sources --cookie "$SESSION"

# Sync schemes
curl -X POST http://localhost:8000/api/admin/schemes/sync --cookie "$SESSION"

# Reconcile vectors
curl -X POST http://localhost:8000/api/admin/knowledge/reconcile-vectors --cookie "$SESSION"
```

## Success Metrics

After full ingestion, expect:
- **Sources**: 23-27 ingested (85%+ success)
- **Documents**: 100-200+
- **Chunks**: 500-2000+
- **Schemes**: 50-100+
- **Categories**: 10-15
- **Vector points**: Matches chunk count

## Scheme Categories (Expected)

1. Cooperatives (10-15 schemes)
2. Agriculture (15-20 schemes)
3. Financial inclusion (5-8 schemes)
4. Fisheries (3-5 schemes)
5. Livestock & Dairy (3-5 schemes)
6. Food processing (3-5 schemes)
7. Tribal welfare (2-4 schemes)
8. Farmer Producer Organisations (2-3 schemes)
9. Irrigation (2-3 schemes)
10. State-specific (5-10 schemes)

## Configuration Checklist

Environment variables required:
- [x] `ASYNC_DATABASE_URL` - PostgreSQL connection
- [x] `QDRANT_URL` - Vector store URL
- [x] `QDRANT_COLLECTION_NAME` - Collection name
- [x] `GOOGLE_APPLICATION_CREDENTIALS` - GCP credentials path
- [x] `GOOGLE_VERTEX_PROJECT_ID` - GCP project
- [x] `GOOGLE_VERTEX_LOCATION` - GCP region
- [x] `GOOGLE_VISION_API_ENABLED` - Enable OCR (optional)

## Monitoring

### Daily Checks
```bash
# Run due source checks (automated via cron/scheduler)
python -m app.knowledge.cli

# Check for failures
psql -c "SELECT source_key, failure_code FROM knowledge_source_checks WHERE result = 'FAILED' ORDER BY checked_at DESC LIMIT 5;"
```

### Weekly Checks
```bash
# Reconcile vectors
python -m app.knowledge.cli --reconcile

# Check scheme growth
psql -c "SELECT COUNT(*) as total_schemes, MAX(created_at) as latest FROM schemes;"
```

### Monthly Checks
```bash
# Full validation
python test_knowledge_pipeline.py

# Review extraction quality
psql -c "SELECT category, AVG(array_length(beneficiary_categories, 1)) as avg_beneficiaries FROM schemes GROUP BY category;"
```

## Support

For detailed help:
- **Ingestion**: See `KNOWLEDGE_INGESTION_GUIDE.md`
- **Testing**: See `TESTING_KNOWLEDGE_PIPELINE.md`
- **Overview**: See `KNOWLEDGE_SYSTEM_SUMMARY.md`

For errors:
1. Check logs in `backend/logs/`
2. Query `knowledge_source_checks` table
3. Review specific error codes in documentation
4. Open issue with error details

## Version Info

- **Sources**: 27 registered (17 new + 10 existing)
- **Categories**: 15+ scheme categories
- **Beneficiaries**: 12+ beneficiary types
- **Languages**: Hindi, English, Marathi
- **Citation Support**: Full URL preservation
- **Last Updated**: 2024
