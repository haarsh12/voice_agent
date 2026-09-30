# Knowledge Ingestion Guide

This guide explains how to ingest government schemes and policies into the Sahayak AI knowledge base (Qdrant vector store and Supabase/PostgreSQL database).

## Overview

Sahayak AI uses a **verified knowledge ingestion pipeline** that:
1. Fetches documents from approved government sources
2. Extracts text content (with OCR support for PDFs)
3. Chunks content semantically
4. Generates embeddings using Vertex AI
5. Stores in PostgreSQL (audit/metadata) and Qdrant (vectors)
6. Extracts scheme information and creates catalogue records
7. Provides citations with URLs in AI responses

## Registered Sources

The system now includes **27 approved sources** covering:

### Cooperative Sector
- Ministry of Cooperation (PACS, computerization, schemes)
- CRCS (Multi-State Cooperative Societies)
- NCDC (Yuva Sahakar, Sahakar Mitra, Dairy Sahakar, Ayushman Sahakar, Digital Sahakar)
- National Cooperative Database

### Agriculture & Farmer Schemes
- PM-KISAN (income support)
- Kisan Credit Card (KCC)
- PMFBY (crop insurance)
- Agriculture Infrastructure Fund (AIF)
- PMKSY (irrigation)
- Soil Health Card
- PKVY (organic farming)
- SMAM (mechanization)
- MIDH (horticulture)
- e-NAM (marketing)
- MSP Operations

### Fisheries, Dairy & Livestock
- Department of Fisheries (PMMSY, FIDF)
- Department of Animal Husbandry & Dairying (Rashtriya Gokul Mission, National Livestock Mission)

### Food Processing & Tribal Welfare
- Ministry of Food Processing (PMFME, Sampada Yojana)
- TRIFED (Van Dhan Vikas Kendra)

### FPO & State-Specific
- FPO Formation Scheme
- Maharashtra Agriculture Department
- Maharashtra Cooperative Department (State RCS)

### Cross-Cutting
- RBI (financial literacy, banking)
- myScheme (scheme discovery portal)
- India Code (legal/regulatory)
- CPGRAMS (grievance system)

## Ingestion Methods

### Method 1: Bulk Ingestion via Batch Script (Recommended for Initial Setup)

**Windows:**
```batch
cd backend
ingest_all_sources.bat
```

This script will:
- Ingest all 27 registered sources
- Extract and store all schemes
- Reconcile vector store
- Take 30-60 minutes depending on network speed

### Method 2: CLI Commands

**Check all due sources (respects check intervals):**
```bash
cd backend
.venv\Scripts\activate
python -m app.knowledge.cli
```

**Force ingest all sources (ignore intervals):**
```bash
python -m app.knowledge.cli --ingest-all
```

**Ingest specific source:**
```bash
python -m app.knowledge.cli --source ncdc
python -m app.knowledge.cli --source pm_kisan
python -m app.knowledge.cli --source pmfby
```

**Available source keys:**
- `ministry_of_cooperation`
- `ncdc`
- `pm_kisan`
- `kisan_credit_card`
- `agriculture_infrastructure_fund`
- `pmksy`
- `pmfby`
- `ministry_of_fisheries`
- `department_animal_husbandry_dairying`
- `food_processing_ministry`
- `trifed`
- `fpo_formation`
- `maharashtra_agriculture`
- `state_rcs`
- `soil_health_card`
- `paramparagat_krishi_vikas`
- `sub_mission_agricultural_mechanization`
- `horticulture_mission`
- `e_nam`
- `minimum_support_price`
- `ministry_of_agriculture`
- `myscheme`
- `reserve_bank_of_india`
- `cpgrams`
- `india_code`
- `national_cooperative_database`
- `central_registrar_of_cooperative_societies`

**Backfill schemes from already-ingested documents:**
```bash
python -m app.knowledge.cli --backfill-schemes
```

**Reconcile vector store (repair missing/stale vectors):**
```bash
python -m app.knowledge.cli --reconcile
```

**Reindex specific source:**
```bash
python -m app.knowledge.cli --reindex-source ncdc
```

### Method 3: Admin API Endpoints

**Start ingestion via API:**
```bash
# Check due sources
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{}' \
  --cookie "admin_session=YOUR_SESSION"

# Force all sources
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_all": true}' \
  --cookie "admin_session=YOUR_SESSION"

# Check specific source
curl -X POST http://localhost:8000/api/admin/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_key": "ncdc"}' \
  --cookie "admin_session=YOUR_SESSION"
```

**List all sources:**
```bash
curl http://localhost:8000/api/admin/knowledge/sources \
  --cookie "admin_session=YOUR_SESSION"
```

**Sync scheme catalog:**
```bash
curl -X POST http://localhost:8000/api/admin/schemes/sync \
  --cookie "admin_session=YOUR_SESSION"
```

**Reconcile vectors:**
```bash
curl -X POST http://localhost:8000/api/admin/knowledge/reconcile-vectors \
  --cookie "admin_session=YOUR_SESSION"
```

## Configuration Requirements

Before running ingestion, ensure these are configured in `.env`:

```env
# Database
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/sahayak

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=sahayak_knowledge

# Google Cloud (for embeddings and OCR)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_VERTEX_PROJECT_ID=your-project-id
GOOGLE_VERTEX_LOCATION=us-central1

# Optional: OCR for scanned PDFs
GOOGLE_VISION_API_ENABLED=true
```

## Verification

After ingestion, verify the results:

### 1. Check Database
```sql
-- Count ingested documents
SELECT source_key, COUNT(*) 
FROM knowledge_documents 
GROUP BY source_key;

-- Count schemes
SELECT category, COUNT(*) 
FROM schemes 
GROUP BY category;

-- Check recent ingestion
SELECT source_key, status, last_checked_at 
FROM knowledge_sources 
ORDER BY last_checked_at DESC;
```

### 2. Check Qdrant
```bash
# Check collection info
curl http://localhost:6333/collections/sahayak_knowledge
```

### 3. Test Voice Agent
Ask questions like:
- "मुझे युवा सहकार योजना के बारे में बताओ" (Tell me about Yuva Sahakar)
- "What is PM-KISAN scheme?"
- "NCDC की कौन सी schemes available हैं?" (What NCDC schemes are available?)
- "Tell me about fisheries schemes"
- "Van Dhan Vikas Kendra क्या है?" (What is Van Dhan Vikas Kendra?)

The agent should:
- Provide accurate information from verified sources
- Show citations with clickable source URLs in the UI
- Label general guidance when official sources aren't available

## Troubleshooting

### Network Timeouts
If sources timeout, check:
- Internet connectivity
- Firewall/proxy settings
- Government website availability
- Increase timeout in settings: `KNOWLEDGE_DOCUMENT_PROCESSING_TIMEOUT_SECONDS`

### OCR Failures
If PDFs fail to extract:
- Ensure `GOOGLE_VISION_API_ENABLED=true`
- Check Google Cloud credentials
- Verify Vision API is enabled in GCP project
- Check PDF quality (some scanned PDFs may be unreadable)

### Vector Store Issues
If Qdrant sync fails:
- Verify Qdrant is running: `docker ps`
- Check `QDRANT_URL` in `.env`
- Run reconciliation: `python -m app.knowledge.cli --reconcile`

### Missing Schemes
If schemes don't appear:
- Run backfill: `python -m app.knowledge.cli --backfill-schemes`
- Check extraction logs for errors
- Verify source documents contain scheme information

## Scheduling Regular Updates

### Windows Task Scheduler
Create a scheduled task to run:
```batch
cd D:\voice_stream\backend
.venv\Scripts\activate && python -m app.knowledge.cli
```
Schedule: Daily at 2 AM

### Linux Cron
```cron
0 2 * * * cd /path/to/voice_stream/backend && .venv/bin/python -m app.knowledge.cli
```

### Docker/Kubernetes
Create a CronJob for periodic ingestion:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: sahayak-knowledge-ingestion
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ingestion
            image: sahayak-backend:latest
            command: ["python", "-m", "app.knowledge.cli"]
```

## Adding New Sources

To add a new government source:

1. **Update registry.py:**
```python
ApprovedSourceDefinition(
    key="new_scheme_portal",
    name="New Scheme Portal",
    category="scheme_category",
    authority_level=100,
    geographic_scope="NATIONAL",
    check_interval_hours=24,
    approved_domains=("scheme.gov.in",),
    crawl_targets=(
        CrawlTarget("https://scheme.gov.in/", ("scheme_info",)),
    ),
    expected_categories=("scheme_info", "guidelines"),
    discovery_path_prefixes=("/documents/", "/pdf/"),
)
```

2. **Update extraction.py (if needed):**
- Add to `dedicated_names` if it's a dedicated portal
- Update `_category`, `_scheme_type`, `_beneficiaries` for proper classification

3. **Test ingestion:**
```bash
python -m app.knowledge.cli --source new_scheme_portal
```

4. **Verify results and commit changes**

## Best Practices

1. **Always run reconciliation after bulk ingestion** to ensure vector consistency
2. **Monitor logs** for extraction failures or network issues
3. **Test with sample queries** before considering ingestion complete
4. **Schedule regular updates** to keep information current
5. **Back up the database** before major re-ingestion operations
6. **Use force ingestion sparingly** - it hits government servers hard
7. **Check government source availability** during Indian business hours
8. **Document any new sources** you add to the registry

## Support

For issues or questions:
- Check logs in `backend/logs/`
- Review source check history in `knowledge_source_checks` table
- Inspect failed documents in `knowledge_documents` with status FETCH_FAILED or EXTRACTION_FAILED
- Open an issue with ingestion logs and error messages
