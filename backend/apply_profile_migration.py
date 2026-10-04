#!/usr/bin/env python3
"""Apply PIN code and email migration to sahayak_accounts table"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings


async def apply_migration():
    """Apply the profile enhancement migration"""
    settings = get_settings()
    
    if not settings.database_url:
        print("❌ DATABASE_URL not configured")
        return 1
    
    print("🔄 Applying profile migration (PIN code + email)...")
    
    # Get the actual string from SecretStr and convert to async driver
    db_url = str(settings.database_url)
    if hasattr(settings.database_url, 'get_secret_value'):
        db_url = settings.database_url.get_secret_value()
    
    # Replace postgresql:// with postgresql+asyncpg://
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    # Create engine
    engine = create_async_engine(db_url, echo=True)
    
    # Read migration file
    migration_file = Path(__file__).parent / "migrations" / "add_pin_code_and_email.sql"
    migration_sql = migration_file.read_text()
    
    try:
        async with engine.begin() as conn:
            # Execute migration
            await conn.execute(text(migration_sql))
            print("\n✅ Migration applied successfully!")
            print("   - Added pin_code column (VARCHAR(6))")
            print("   - Added email column (VARCHAR(254))")
            
        await engine.dispose()
        return 0
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        await engine.dispose()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(apply_migration()))
