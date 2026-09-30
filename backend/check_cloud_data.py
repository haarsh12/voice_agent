"""Check what data exists in Supabase and Qdrant Cloud"""
import asyncio
import httpx
from app.config.settings import get_settings
from app.auth.session import get_session_factory
from sqlalchemy import text

async def check():
    settings = get_settings()
    
    print("\n" + "="*60)
    print("CLOUD DATA STATUS CHECK")
    print("="*60)
    
    # Check Supabase
    print("\n📊 SUPABASE (PostgreSQL):")
    print("-" * 60)
    
    if not settings.async_database_url or "[YOUR-" in settings.async_database_url:
        print("❌ DATABASE_URL not configured properly in .env")
        print("   Please set your actual Supabase connection string")
        return
    
    try:
        factory = get_session_factory()
        async with factory() as session:
            # Check knowledge data
            sources = await session.execute(text("SELECT COUNT(DISTINCT source_key) FROM sahayak_knowledge_sources"))
            docs = await session.execute(text("SELECT COUNT(*) FROM sahayak_knowledge_documents"))
            chunks = await session.execute(text("SELECT COUNT(*) FROM sahayak_knowledge_chunks"))
            schemes = await session.execute(text("SELECT COUNT(*) FROM sahayak_schemes"))
            
            sources_count = sources.scalar() or 0
            docs_count = docs.scalar() or 0
            chunks_count = chunks.scalar() or 0
            schemes_count = schemes.scalar() or 0
            
            print(f"✅ Connected successfully!")
            print(f"   Sources registered: {sources_count}")
            print(f"   Documents: {docs_count}")
            print(f"   Chunks: {chunks_count}")
            print(f"   Schemes: {schemes_count}")
            
            if sources_count > 0:
                print("\n   Top sources:")
                result = await session.execute(text("""
                    SELECT s.key, s.name, 
                           (SELECT COUNT(*) FROM sahayak_knowledge_documents d WHERE d.source_key = s.key) as doc_count
                    FROM sahayak_knowledge_sources s
                    ORDER BY s.last_checked_at DESC NULLS LAST
                    LIMIT 5
                """))
                for row in result:
                    print(f"   - {row[0]}: {row[1]} ({row[2]} docs)")
                    
    except Exception as e:
        print(f"❌ Supabase Error: {e}")
        print("   Check your DATABASE_URL in .env file")
    
    # Check Qdrant Cloud
    print("\n🔍 QDRANT CLOUD (Vector Store):")
    print("-" * 60)
    
    if not settings.qdrant_url:
        print("❌ QDRANT_URL not configured")
        return
    
    try:
        headers = {}
        if settings.qdrant_api_key:
            headers["api-key"] = settings.qdrant_api_key.get_secret_value()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check collection
            response = await client.get(
                f"{settings.qdrant_url}/collections/{settings.qdrant_collection}",
                headers=headers
            )
            
            if response.status_code == 404:
                print(f"⚠️  Collection '{settings.qdrant_collection}' doesn't exist yet")
                print("   It will be created automatically during first ingestion")
            elif response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                vectors_count = result.get("vectors_count", 0)
                points_count = result.get("points_count", 0)
                
                print(f"✅ Connected successfully!")
                print(f"   Collection: {settings.qdrant_collection}")
                print(f"   Vectors: {vectors_count:,}")
                print(f"   Points: {points_count:,}")
                
                if points_count == 0:
                    print("\n   ⚠️  No vectors yet - run ingestion to populate")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"❌ Qdrant Error: {e}")
        print("   Check QDRANT_URL and QDRANT_API_KEY in .env")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    if docs_count > 0 and chunks_count > 0:
        print("✅ DATA EXISTS in Supabase")
        print("✅ System can retrieve knowledge and provide citations")
        if points_count > 0:
            print("✅ Vectors exist in Qdrant - full RAG operational!")
        else:
            print("⚠️  No vectors in Qdrant yet - vector search unavailable")
            print("   Run: python -m app.knowledge.cli --reconcile")
    else:
        print("⚠️  NO DATA in Supabase yet")
        print("   Run ingestion to populate:")
        print("   python -m app.knowledge.cli --source cpgrams")
    
    print("\nNext steps:")
    if docs_count == 0:
        print("1. Run: python -m app.knowledge.cli --source cpgrams")
        print("2. Run: python -m app.knowledge.cli --backfill-schemes")
        print("3. Test: python check_retrieval.py")
    else:
        print("1. Test retrieval: python check_retrieval.py")
        print("2. Add more sources: python -m app.knowledge.cli --source <name>")
        print("3. Test voice agent with citations")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(check())
