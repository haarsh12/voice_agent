# Setup: Supabase + Qdrant Cloud Configuration

## Current Status
✅ Qdrant Cloud configured  
✅ Google Cloud configured  
⚠️ Supabase DATABASE_URL needed

## Step 1: Get Supabase Connection String

1. Go to your Supabase project: https://supabase.com/dashboard/project/YOUR_PROJECT
2. Click "Project Settings" (gear icon bottom left)
3. Click "Database" tab
4. Scroll to "Connection string" section
5. Select "URI" tab
6. Copy the connection string (looks like):
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```
7. **IMPORTANT**: Replace `[YOUR-PASSWORD]` with your actual database password

## Step 2: Update .env File

Open `backend/.env` and replace this line:
```env
DATABASE_URL=postgresql://postgres:[YOUR-SUPABASE-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

With your actual connection string from Step 1.

## Step 3: Create Database Schema in Supabase

Run this command to create all tables in Supabase:

```bash
cd backend
.venv\Scripts\python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; from app.auth.models import AuthBase; import app.knowledge.models; import app.grievances.models; from app.config.settings import get_settings; async def setup(): engine = create_async_engine(get_settings().async_database_url); async with engine.begin() as conn: await conn.run_sync(AuthBase.metadata.create_all); print('✓ All tables created in Supabase!'); asyncio.run(setup())"
```

Or use this script:
```bash
cd backend
.venv\Scripts\python setup_supabase.py
```

## Step 4: Verify Qdrant Cloud Connection

```bash
curl https://99864a19-ec64-4d87-8051-1687605326b5.us-east-1-1.aws.cloud.qdrant.io:6333/collections \
  -H "api-key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Expected: List of collections (may be empty)

## Step 5: Run Initial Data Ingestion

This will:
- Fetch documents from government sources
- Store metadata in Supabase (PostgreSQL)
- Store vectors in Qdrant Cloud
- Extract schemes

### Option A: Quick Test (1 source, 2-3 minutes)
```bash
cd backend
.venv\Scripts\python -m app.knowledge.cli --source cpgrams
.venv\Scripts\python -m app.knowledge.cli --backfill-schemes
```

### Option B: Full Ingestion (27 sources, 30-60 minutes)
```bash
cd backend
ingest_all_sources.bat
```

## Step 6: Verify Data is in Cloud

### Check Supabase
Go to Supabase → Table Editor and verify you see:
- `sahayak_knowledge_sources`
- `sahayak_knowledge_documents`
- `sahayak_knowledge_chunks`
- `sahayak_schemes`

### Check Qdrant
```bash
curl https://YOUR-QDRANT-URL:6333/collections/sahayak_verified_knowledge \
  -H "api-key: YOUR-API-KEY"
```

Should show: `"vectors_count": >0, "points_count": >0`

## Step 7: Test RAG System

### Test Retrieval
```bash
cd backend
.venv\Scripts\python -c "
import asyncio
from app.auth.session import get_session_factory
from app.config.settings import get_settings
from app.knowledge.retrieval import KnowledgeRetriever

async def test():
    settings = get_settings()
    async with get_session_factory()() as session:
        retriever = KnowledgeRetriever(session, settings)
        result = await retriever.retrieve('NCDC schemes')
        print(f'Evidence: {len(result.evidence)} items')
        print(f'Citations: {len(result.citations)}')
        if result.citations:
            print(f'First source: {result.citations[0].source_name}')
            print(f'URL: {result.citations[0].url}')

asyncio.run(test())
"
```

Expected output:
```
Evidence: 5-8 items
Citations: 3-6
First source: Ministry of Cooperation (or similar)
URL: https://cooperation.gov.in/... (or similar)
```

### Test Voice Agent
1. Start backend: `start_complete_backend.bat`
2. Start frontend: `cd frontend; npm run dev`
3. Start agent: `cd backend; .venv\Scripts\python -m app.agent.runner dev`
4. Open http://localhost:5173
5. Ask: "मुझे युवा सहकार योजना के बारे में बताओ"
6. Expected: Answer with citations showing URLs

## Architecture Summary

```
Government Sources (27)
        ↓
Ingestion CLI (.venv\Scripts\python -m app.knowledge.cli)
        ↓
    ┌───────────────┐
    ↓               ↓
Supabase         Qdrant Cloud
(PostgreSQL)     (Vectors)
    ↓               ↓
Knowledge Retrieval
    ↓
Voice Agent
    ↓
User + Citations
```

## Data Storage

### In Supabase (PostgreSQL):
- Document metadata (URLs, titles, versions)
- Chunks (text content)
- Schemes (catalogue)
- Source audit history
- Citations with URLs

### In Qdrant Cloud (Vectors):
- 768-dimensional embeddings
- Vector search index
- Metadata for filtering

### NOT Stored Locally:
- ❌ No knowledge data on laptop
- ✅ All data in cloud (Supabase + Qdrant)
- ✅ Agent retrieves from cloud in real-time

## Troubleshooting

### "no such table" error
→ DATABASE_URL not set correctly
→ Run Step 2 and Step 3 again

### "Connection refused" to Qdrant
→ Check QDRANT_URL and QDRANT_API_KEY in .env
→ Verify Qdrant cluster is running

### "Embedding failed"
→ Check GOOGLE_APPLICATION_CREDENTIALS
→ Verify Vertex AI API is enabled in Google Cloud

### No citations in responses
→ Check data was ingested (Step 5)
→ Verify retrieval works (Step 7)
→ Check frontend console for errors

## Next Steps

Once setup is complete:
1. Schedule daily ingestion: `python -m app.knowledge.cli` (checks due sources)
2. Monitor Supabase usage (Database → Reports)
3. Monitor Qdrant usage (Qdrant console)
4. Test with real users
5. Add more sources as needed
