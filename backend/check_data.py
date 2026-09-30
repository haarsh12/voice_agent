import asyncio
from app.auth.session import get_session_factory
from sqlalchemy import text

async def check():
    factory = get_session_factory()
    async with factory() as session:
        sources = await session.execute(text('SELECT COUNT(DISTINCT source_key) FROM knowledge_documents'))
        docs = await session.execute(text('SELECT COUNT(*) FROM knowledge_documents'))
        chunks = await session.execute(text('SELECT COUNT(*) FROM knowledge_chunks'))
        schemes = await session.execute(text('SELECT COUNT(*) FROM sahayak_schemes'))
        
        print(f'\n=== DATABASE STATUS ===')
        print(f'Sources with data: {sources.scalar()}')
        print(f'Total documents: {docs.scalar()}')
        print(f'Total chunks: {chunks.scalar()}')
        print(f'Total schemes: {schemes.scalar()}')
        print('=====================\n')

asyncio.run(check())
