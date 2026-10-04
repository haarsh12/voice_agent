#!/usr/bin/env python3
"""Apply enhanced profile fields migration to sahayak_accounts table"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import get_settings


async def apply_migration():
    """Apply the enhanced profile migration"""
    settings = get_settings()
    
    if not settings.database_url:
        print("❌ DATABASE_URL not configured")
        return 1
    
    print("🔄 Applying enhanced profile migration...")
    print("   Adding: date_of_birth, pin_code, email")
    
    # Get the actual string from SecretStr and convert to async driver
    db_url = str(settings.database_url)
    if hasattr(settings.database_url, 'get_secret_value'):
        db_url = settings.database_url.get_secret_value()
    
    # Replace postgresql:// with postgresql+asyncpg://
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    # Create engine
    engine = create_async_engine(db_url, echo=False)
    
    # Read migration file
    migration_file = Path(__file__).parent / "migrations" / "add_enhanced_profile_fields.sql"
    migration_sql = migration_file.read_text()
    
    # Split into individual statements
    statements = [
        stmt.strip() 
        for stmt in migration_sql.split(';') 
        if stmt.strip() and not stmt.strip().startswith('--')
    ]
    
    try:
        async with engine.begin() as conn:
            # Execute each statement separately
            for stmt in statements:
                if stmt:
                    await conn.execute(text(stmt))
            
            print("\n✅ Migration applied successfully!")
            print("   ✓ date_of_birth column added")
            print("   ✓ pin_code column added (VARCHAR(6))")
            print("   ✓ email column added (VARCHAR(254))")
            print("   ✓ Index created on date_of_birth")
            
        await engine.dispose()
        return 0
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        await engine.dispose()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(apply_migration()))
