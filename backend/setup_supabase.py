"""Create all database tables in Supabase"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.auth.models import AuthBase
import app.knowledge.models  # Register knowledge tables
import app.grievances.models  # Register grievance tables
from app.config.settings import get_settings

async def setup():
    settings = get_settings()
    
    if not settings.async_database_url:
        print("❌ DATABASE_URL not configured in .env file!")
        print("Please add your Supabase connection string:")
        print("DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres")
        return
    
    if "sqlite" in settings.async_database_url:
        print("⚠️  WARNING: Using local SQLite database, not Supabase!")
        print("To use Supabase, set DATABASE_URL in .env file")
        return
    
    print(f"Connecting to: {settings.async_database_url.split('@')[1].split('/')[0]}...")
    
    engine = create_async_engine(settings.async_database_url)
    
    try:
        async with engine.begin() as conn:
            print("Creating all tables in Supabase...")
            await conn.run_sync(AuthBase.metadata.create_all)
            print("\n✅ SUCCESS! All tables created in Supabase:")
            print("   - sahayak_accounts")
            print("   - sahayak_knowledge_sources")
            print("   - sahayak_knowledge_documents")
            print("   - sahayak_knowledge_document_versions")
            print("   - sahayak_knowledge_chunks")
            print("   - sahayak_knowledge_source_checks")
            print("   - sahayak_knowledge_failed_resources")
            print("   - sahayak_schemes")
            print("   - sahayak_scheme_versions")
            print("   - sahayak_scheme_sources")
            print("   - sahayak_grievances")
            print("   - sahayak_grievance_events")
            print("   - (and other auth tables)")
            print("\nNext step: Run data ingestion to populate the tables")
            print("  python -m app.knowledge.cli --source cpgrams")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check your DATABASE_URL is correct")
        print("2. Verify Supabase project is active")
        print("3. Check database password is correct")
        print("4. Ensure your IP is allowed (Supabase → Project Settings → Database → Connection Pooling)")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup())
