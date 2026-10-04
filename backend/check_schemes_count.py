#!/usr/bin/env python3
"""Quick check of schemes in database"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings


async def check_schemes():
    settings = get_settings()
    
    # Get the actual string from SecretStr and convert to async driver
    db_url = str(settings.database_url)
    if hasattr(settings.database_url, 'get_secret_value'):
        db_url = settings.database_url.get_secret_value()
    
    # Replace postgresql:// with postgresql+asyncpg://
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(db_url, echo=False)
    
    async with engine.begin() as conn:
        # Count total schemes
        result = await conn.execute(
            text('SELECT COUNT(*) FROM sahayak_schemes')
        )
        total_schemes = result.scalar()
        
        # Count current/approved versions
        result = await conn.execute(
            text("""
                SELECT COUNT(*) 
                FROM sahayak_scheme_versions 
                WHERE is_current = true 
                AND verification_status = 'APPROVED'
            """)
        )
        approved_current = result.scalar()
        
        print(f"\n📊 Schemes Database Status:")
        print(f"   Total schemes: {total_schemes}")
        print(f"   Approved & current versions: {approved_current}")
        
        if approved_current == 0:
            print(f"\n⚠️  NO APPROVED SCHEMES FOUND!")
            print(f"   This is why guest mode shows '0 verified records'")
            print(f"   You need to ingest scheme data first.")
        else:
            print(f"\n✅ Schemes are available in database")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_schemes())
