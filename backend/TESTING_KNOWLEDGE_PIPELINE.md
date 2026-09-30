# Knowledge Ingestion Pipeline Testing Guide

This document provides a comprehensive testing plan for validating the complete knowledge ingestion pipeline from source fetching to AI responses with citations.

## Testing Overview

The pipeline has 7 major stages to test:
1. **Source Registry** - Verify all sources are registered correctly
2. **Document Fetching** - Test document retrieval from government sources
3. **Content Extraction** - Validate text extraction and OCR
4. **Chunking** - Verify semantic chunking quality
5. **Vector Indexing** - Test Qdrant storage and embeddings
6. **Scheme Extraction** - Validate scheme catalogue creation
7. **End-to-End Retrieval** - Test AI responses with proper citations

## Prerequisites

Before testing, ensure:
- [ ] Backend is running (`uvicorn app.main:app --reload`)
- [ ] Qdrant is running (`docker ps` should show qdrant container)
- [ ] Database is accessible
- [ ] Google Cloud credentials are configured
- [ ] `.env` file has all required settings

## Test Plan

### Stage 1: Verify Source Registry

**Objective:** Confirm all 27 sources are registered with correct configuration

**Test Commands:**
```bash
# List all registered sources
python -c "from app.knowledge.registry import SOURCE_REGISTRY; print(f'Total sources: {len(SOURCE_REGISTRY)}'); [print(f'{s.key}: {s.name} ({s.category})') for s in SOURCE_REGISTRY]"

# Or via API
curl http://localhost:8000/api/admin/knowledge/sources
```

**Expected Results:**
- Total sources: 27
- Sources include:
  - ✓ ministry_of_cooperation
  - ✓ ncdc (NCDC schemes)
  - ✓ pm_kisan (PM-KISAN)
  - ✓ kisan_credit_card (KCC)
  - ✓ agriculture_infrastructure_fund (AIF)
  - ✓ pmksy (irrigation)
  - ✓ pmfby (crop insurance)
  - ✓ ministry_of_fisheries (PMMSY, FIDF)
  - ✓ department_animal_husbandry_dairying (livestock/dairy)
  - ✓ food_processing_ministry (PMFME, Sampada)
  - ✓ trifed (Van Dhan Vikas)
  - ✓ fpo_formation
  - ✓ maharashtra_agriculture
  - ✓ state_rcs (Maharashtra cooperatives)
  - ✓ soil_health_card
  - ✓ paramparagat_krishi_vikas (PKVY)
  - ✓ sub_mission_agricultural_mechanization (SMAM)
  - ✓ horticulture_mission (MIDH)
  - ✓ e_nam
  - ✓ minimum_support_price (MSP)
  - Plus 7 existing sources

**Pass Criteria:**
- All 27 sources listed
- Each has approved_domains, crawl_targets, expected_categories
- Authority levels are set (95-100)
- Geographic scope is defined

---

### Stage 2: Test Single Source Ingestion

**Objective:** Verify document fetching and basic ingestion for one source

**Test Command:**
```bash
# Test with a reliable, fast source
python -m app.knowledge.cli --source cpgrams
```

**Monitor Logs For:**
```
knowledge_source_check_complete source=cpgrams result=CHANGED
```

**Expected Results:**
- Documents fetched from pgportal.gov.in
- Status: CHANGED or UNCHANGED (both are success)
- No FETCH_FAILED or EXTRACTION_FAILED errors

**Database Verification:**
```sql
-- Check ingested documents
SELECT 
    d.id,
    d.canonical_url,
    v.title,
    v.status,
    v.created_at
FROM knowledge_documents d
JOIN knowledge_document_versions v ON v.document_id = d.id
WHERE d.source_key = 'cpgrams'
    AND v.status = 'CURRENT'
ORDER BY v.created_at DESC
LIMIT 5;

-- Check chunks
SELECT COUNT(*) as chunk_count
FROM knowledge_chunks c
JOIN knowledge_document_versions v ON v.id = c.document_version_id
JOIN knowledge_documents d ON d.id = v.document_id
WHERE d.source_key = 'cpgrams';
```

**Pass Criteria:**
- At least 1 document ingested
- Status is CURRENT
- Multiple chunks created (at least 5-10 per document)

---

### Stage 3: Test NCDC Source (Critical for New Schemes)

**Objective:** Validate NCDC scheme ingestion with Yuva Sahakar, Sahakar Mitra, etc.

**Test Command:**
```bash
python -m app.knowledge.cli --source ncdc
```

**Expected Results:**
- Documents fetched from ncdc.in
- Schemes extracted: Yuva Sahakar, Sahakar Mitra, Dairy Sahakar, Ayushman Sahakar
- Category: cooperative_financing

**Database Verification:**
```sql
-- Check NCDC documents
SELECT v.title, v.coverage_categories
FROM knowledge_document_versions v
JOIN knowledge_documents d ON d.id = v.document_id
WHERE d.source_key = 'ncdc' AND v.status = 'CURRENT';

-- Check extracted NCDC schemes
SELECT 
    official_name,
    scheme_type,
    category,
    beneficiary_categories
FROM schemes
WHERE official_name ILIKE '%sahakar%'
   OR official_name ILIKE '%ncdc%';
```

**Pass Criteria:**
- At least 1 NCDC document ingested
- Schemes contain "Sahakar" keywords
- Category is "Cooperatives" or related
- Beneficiaries include "cooperative_member", "cooperative_official"

---

### Stage 4: Test Agriculture Schemes

**Objective:** Validate PM-KISAN and agriculture scheme ingestion

**Test Commands:**
```bash
# PM-KISAN
python -m app.knowledge.cli --source pm_kisan

# KCC
python -m app.knowledge.cli --source kisan_credit_card

# PMKSY
python -m app.knowledge.cli --source pmksy
```

**Expected Schemes:**
- Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)
- Kisan Credit Card (KCC)
- Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)

**Database Verification:**
```sql
SELECT 
    official_name,
    category,
    scheme_type,
    geographic_scope,
    array_length(beneficiary_categories, 1) as beneficiary_count
FROM schemes
WHERE official_name ILIKE '%kisan%'
   OR official_name ILIKE '%krishi%'
ORDER BY official_name;
```

**Pass Criteria:**
- PM-KISAN scheme created with category "Income support"
- KCC scheme with category "Financial inclusion"
- PMKSY scheme with category "Irrigation"
- Beneficiaries include "farmer"

---

### Stage 5: Test Fisheries and Livestock Schemes

**Objective:** Validate specialized sector scheme ingestion

**Test Commands:**
```bash
# Fisheries
python -m app.knowledge.cli --source ministry_of_fisheries

# Dairy & Livestock
python -m app.knowledge.cli --source department_animal_husbandry_dairying
```

**Expected Schemes:**
- PMMSY (Pradhan Mantri Matsya Sampada Yojana)
- FIDF (Fisheries Infrastructure Development Fund)
- Rashtriya Gokul Mission
- National Livestock Mission

**Database Verification:**
```sql
SELECT 
    official_name,
    category,
    beneficiary_categories
FROM schemes
WHERE category IN ('Fisheries', 'Livestock & Dairy')
   OR official_name ILIKE '%matsya%'
   OR official_name ILIKE '%gokul%'
   OR official_name ILIKE '%livestock%';
```

**Pass Criteria:**
- Fisheries schemes have category "Fisheries"
- Beneficiaries include "fisheries_stakeholder"
- Livestock schemes have category "Livestock & Dairy"
- Beneficiaries include "dairy_livestock_farmer"

---

### Stage 6: Test Maharashtra-Specific Schemes

**Objective:** Validate state-specific scheme ingestion

**Test Commands:**
```bash
# Maharashtra Agriculture
python -m app.knowledge.cli --source maharashtra_agriculture

# Maharashtra Cooperatives
python -m app.knowledge.cli --source state_rcs
```

**Expected Results:**
- Schemes with applicable_states = ['Maharashtra']
- Geographic scope = STATE
- State-specific scheme names (Chhatrapati Shivaji, Mahatma Jyotiba Phule)

**Database Verification:**
```sql
SELECT 
    official_name,
    category,
    geographic_scope,
    applicable_states
FROM schemes
WHERE geographic_scope = 'STATE'
   OR 'Maharashtra' = ANY(applicable_states);
```

**Pass Criteria:**
- At least 1 scheme with Maharashtra in applicable_states
- Category is "State-specific" or specific domain
- Geographic scope is STATE

---

### Stage 7: Test Vector Store Integration

**Objective:** Verify embeddings are created and stored in Qdrant

**Test Commands:**
```bash
# Check Qdrant collection
curl http://localhost:6333/collections/sahayak_knowledge

# Reconcile vectors
python -m app.knowledge.cli --reconcile
```

**Expected Results:**
```json
{
  "status": "ok",
  "result": {
    "vectors_count": 1000,  // Should be > 0
    "indexed_vectors_count": 1000,
    "points_count": 1000
  }
}
```

**Database Cross-Check:**
```sql
-- Count chunks that should have vectors
SELECT COUNT(*) as total_chunks
FROM knowledge_chunks c
JOIN knowledge_document_versions v ON v.id = c.document_version_id
WHERE v.status = 'CURRENT';
```

**Pass Criteria:**
- Qdrant points_count matches or is close to total_chunks
- Reconciliation shows 0 or few missing vectors
- No errors during reconciliation

---

### Stage 8: Test Scheme Backfill

**Objective:** Verify scheme catalogue is populated from knowledge base

**Test Command:**
```bash
python -m app.knowledge.cli --backfill-schemes
```

**Expected Output:**
```
scheme_catalog_backfill_complete changed=50
```

**Database Verification:**
```sql
-- Count schemes by category
SELECT 
    category,
    COUNT(*) as scheme_count
FROM schemes
GROUP BY category
ORDER BY scheme_count DESC;

-- Verify scheme sources
SELECT 
    s.official_name,
    COUNT(DISTINCT ss.chunk_id) as evidence_count
FROM schemes s
LEFT JOIN scheme_sources ss ON ss.scheme_id = s.id
GROUP BY s.id, s.official_name
HAVING COUNT(DISTINCT ss.chunk_id) = 0
LIMIT 10;
```

**Pass Criteria:**
- At least 40-50 schemes created
- Multiple categories represented:
  - Cooperatives (>5 schemes)
  - Agriculture (>10 schemes)
  - Financial inclusion (>3 schemes)
  - Fisheries, Livestock & Dairy, Food processing, etc.
- Most schemes have evidence (chunk_id count > 0)

---

### Stage 9: Test End-to-End Retrieval

**Objective:** Verify knowledge retrieval with proper citations

**Python Test Script:**
```python
import asyncio
from app.auth.session import get_session_factory
from app.config.settings import get_settings
from app.knowledge.retrieval import KnowledgeRetriever
from app.knowledge.contracts import UserKnowledgeContext

async def test_retrieval():
    settings = get_settings()
    factory = get_session_factory()
    
    test_queries = [
        "Tell me about Yuva Sahakar scheme",
        "PM-KISAN के बारे में बताओ",
        "What is PMMSY?",
        "NCDC की schemes कौन सी हैं",
        "Maharashtra में farmers के लिए क्या schemes हैं",
        "Cooperative financing options",
        "Fisheries infrastructure support",
        "Van Dhan Vikas Kendra",
    ]
    
    async with factory() as session:
        retriever = KnowledgeRetriever(session, settings)
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            result = await retriever.retrieve(query)
            
            print(f"Evidence count: {len(result.evidence)}")
            print(f"Citations: {len(result.citations)}")
            
            for i, citation in enumerate(result.citations[:3], 1):
                print(f"\nCitation {i}:")
                print(f"  Source: {citation.source_name}")
                print(f"  Title: {citation.title}")
                print(f"  URL: {citation.url}")
            
            if result.evidence:
                print(f"\nFirst evidence snippet:")
                print(f"  {result.evidence[0].text[:200]}...")

asyncio.run(test_retrieval())
```

**Run Test:**
```bash
cd backend
.venv\Scripts\activate
python test_retrieval.py
```

**Pass Criteria:**
- Each query returns at least 1 evidence item
- Citations include proper source_name, title, and URL
- URLs are government domains (*.gov.in)
- Evidence text is relevant to query
- No "unavailable_reason" errors

---

### Stage 10: Test Voice Agent Responses with Citations

**Objective:** Validate end-to-end AI responses with proper citations in frontend

**Manual Test Steps:**

1. **Start the application:**
   ```bash
   # Terminal 1: Backend
   cd backend
   .venv\Scripts\activate
   uvicorn app.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   
   # Terminal 3: Agent
   cd backend
   python -m app.agent.runner dev
   ```

2. **Open browser and test queries:**

   **Test Query 1: NCDC Scheme**
   - Ask: "मुझे युवा सहकार योजना के बारे में बताओ"
   - Expected:
     - Response mentions Yuva Sahakar
     - Citation shown with NCDC as source
     - Clickable URL to ncdc.in

   **Test Query 2: PM-KISAN**
   - Ask: "What is PM-KISAN scheme?"
   - Expected:
     - Response explains income support
     - Citation shows PM-KISAN portal
     - URL to pmkisan.gov.in

   **Test Query 3: Fisheries**
   - Ask: "Tell me about PMMSY scheme"
   - Expected:
     - Response about fisheries development
     - Citation from Department of Fisheries
     - URL to dof.gov.in

   **Test Query 4: Maharashtra Specific**
   - Ask: "Maharashtra में किसानों के लिए क्या योजनाएं हैं?"
   - Expected:
     - Response lists Maharashtra schemes
     - Citations from Maharashtra government
     - URLs to maharashtra.gov.in domains

   **Test Query 5: Cooperative**
   - Ask: "NCDC से loan कैसे मिलता है?"
   - Expected:
     - Response about NCDC financing
     - Multiple citations if available
     - Proper source attribution

3. **Verify Citation Display:**
   - [ ] Citations appear below the AI response
   - [ ] Source name is visible
   - [ ] Title is descriptive
   - [ ] URL is clickable
   - [ ] URL opens correct government page
   - [ ] "General Guidance" label shows when no official sources found

4. **Verify Agent Behavior:**
   - [ ] Agent doesn't speak URLs aloud
   - [ ] Agent says "I don't have this specific detail" when info not available
   - [ ] Agent labels general guidance clearly
   - [ ] Agent keeps responses concise (voice-appropriate)

**Pass Criteria:**
- All 5 test queries return relevant responses
- Citations display properly with URLs
- URLs are clickable and valid
- Agent behavior matches prompts (no URL speaking, proper abstentions)
- No errors in console or backend logs

---

### Stage 11: Bulk Ingestion Test

**Objective:** Test complete bulk ingestion of all sources

**Test Command:**
```bash
# Run bulk ingestion (30-60 minutes)
cd backend
ingest_all_sources.bat
```

**Monitor Progress:**
- Watch for progress logs: "progress=1/27", "progress=2/27", etc.
- Check for failures
- Note which sources complete successfully

**Post-Ingestion Verification:**

```sql
-- Overall statistics
SELECT 
    'Sources' as type, 
    COUNT(DISTINCT source_key) as count
FROM knowledge_documents
UNION ALL
SELECT 
    'Documents', 
    COUNT(*)
FROM knowledge_document_versions
WHERE status = 'CURRENT'
UNION ALL
SELECT 
    'Chunks', 
    COUNT(*)
FROM knowledge_chunks c
JOIN knowledge_document_versions v ON v.id = c.document_version_id
WHERE v.status = 'CURRENT'
UNION ALL
SELECT 
    'Schemes', 
    COUNT(*)
FROM schemes;

-- Scheme distribution
SELECT 
    category,
    COUNT(*) as schemes,
    COUNT(DISTINCT applicable_states) as states
FROM schemes
GROUP BY category
ORDER BY schemes DESC;

-- Source coverage
SELECT 
    source_key,
    COUNT(DISTINCT d.id) as documents,
    MAX(v.last_checked_at) as last_check
FROM knowledge_documents d
JOIN knowledge_document_versions v ON v.document_id = d.id
WHERE v.status = 'CURRENT'
GROUP BY source_key
ORDER BY documents DESC;
```

**Pass Criteria:**
- At least 23/27 sources ingested successfully (allowing for some timeouts/errors)
- Total documents > 100
- Total chunks > 500
- Total schemes > 50
- Multiple categories represented
- Each scheme category has at least 2 schemes
- Last check timestamps are recent

---

## Troubleshooting Common Issues

### Issue: Documents Not Fetching
**Symptoms:** FETCH_FAILED status, network errors
**Solutions:**
- Check internet connectivity
- Verify government sites are accessible (try in browser)
- Check firewall/proxy settings
- Retry during Indian business hours (IST)

### Issue: OCR Failures
**Symptoms:** EXTRACTION_FAILED for PDFs
**Solutions:**
- Check `GOOGLE_VISION_API_ENABLED=true`
- Verify Google Cloud credentials
- Enable Vision API in GCP project
- Some PDFs may be genuinely unreadable

### Issue: Missing Vectors
**Symptoms:** Qdrant count < chunk count
**Solutions:**
```bash
python -m app.knowledge.cli --reconcile
```

### Issue: No Schemes Extracted
**Symptoms:** Scheme count = 0 after ingestion
**Solutions:**
```bash
python -m app.knowledge.cli --backfill-schemes
```
- Check extraction logs for errors
- Verify source documents contain scheme information

### Issue: No Citations in Responses
**Symptoms:** AI responds but no sources shown
**Solutions:**
- Check retrieval is working (Stage 9 test)
- Verify frontend is receiving data channel messages
- Check browser console for errors
- Ensure LiveKit agent is running

---

## Success Metrics

After completing all tests, the system should achieve:

- ✓ **27 sources** registered and configured
- ✓ **23+ sources** successfully ingested (85%+ success rate)
- ✓ **100+ documents** in knowledge base
- ✓ **500+ chunks** with embeddings
- ✓ **50+ schemes** in catalogue
- ✓ **10+ categories** represented
- ✓ **Citations display** properly in frontend
- ✓ **URLs clickable** and valid
- ✓ **Agent responses** accurate and concise
- ✓ **Abstentions** work when info unavailable

---

## Reporting Results

Document test results using this template:

```markdown
## Knowledge Pipeline Test Results

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Environment:** Development/Production

### Summary
- Total Sources Tested: X/27
- Successful Ingestions: X
- Failed Ingestions: X
- Total Schemes Extracted: X
- Citation Display: ✓/✗

### Detailed Results

#### Stage 1: Source Registry
- Status: PASS/FAIL
- Notes: [any issues]

#### Stage 2-11: [Continue for each stage]
...

### Issues Found
1. [Issue description]
   - Severity: High/Medium/Low
   - Resolution: [how it was fixed]

### Recommendations
- [Any improvements needed]

### Sign-off
- [ ] All critical tests passed
- [ ] Documentation updated
- [ ] Ready for deployment
```

---

## Continuous Testing

For ongoing validation:

1. **Weekly Ingestion Test:**
   - Run bulk ingestion weekly
   - Monitor success rates
   - Track new schemes added

2. **Daily Health Check:**
   ```bash
   python -m app.knowledge.cli
   curl http://localhost:6333/collections/sahayak_knowledge
   ```

3. **Monthly Full Validation:**
   - Run complete test plan (Stages 1-11)
   - Update test queries based on new schemes
   - Verify citation quality

---

## Next Steps After Testing

Once all tests pass:

1. **Schedule regular ingestion:**
   - Set up cron job or scheduled task
   - Run daily at 2 AM IST

2. **Monitor in production:**
   - Set up alerts for ingestion failures
   - Track scheme catalogue growth
   - Monitor citation quality

3. **Iterate on extraction:**
   - Add new sources as identified
   - Improve categorization based on user feedback
   - Enhance beneficiary identification

4. **User acceptance testing:**
   - Get real users to test queries
   - Collect feedback on response quality
   - Validate citation usefulness
