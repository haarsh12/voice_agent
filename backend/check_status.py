"""Quick status check"""
import asyncio
from app.auth.session import get_session_factory
from sqlalchemy import text

async def check():
    async with get_session_factory()() as session:
        sources = await session.execute(text("SELECT COUNT(*) FROM sahayak_knowledge_sources"))
        docs = await session.execute(text("SELECT COUNT(*) FROM sahayak_knowledge_documents"))
        chunks = await session.execute(text("SELECT COUNT(*) FROM sahayak_knowledge_chunks"))
        schemes = await session.execute(text("SELECT COUNT(*) FROM sahayak_schemes"))
        
        print(f"\n📊 SUPABASE STATUS:")
        print(f"  Sources: {sources.scalar()}")
        print(f"  Documents: {docs.scalar()}")
        print(f"  Chunks: {chunks.scalar()}")
        print(f"  Schemes: {schemes.scalar()}\n")

asyncio.run(check())
