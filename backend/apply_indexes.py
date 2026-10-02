#!/usr/bin/env python3
"""Apply performance indexes to the database."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

from app.auth.session import get_engine


async def apply_indexes():
    """Apply all performance indexes from the migration file."""
    engine = get_engine()
    
    if engine is None:
        print("❌ Database engine not configured")
        sys.exit(1)
    
    migration_file = Path(__file__).parent / "migrations" / "add_performance_indexes.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"📁 Reading migration from: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # For SQLite, remove CONCURRENTLY keyword
    is_sqlite = str(engine.url).startswith('sqlite')
    if is_sqlite:
        print("🔧 Detected SQLite - removing CONCURRENTLY keywords")
        sql_content = sql_content.replace(' CONCURRENTLY', '')
    
    # Split into individual statements
    statements = []
    for statement in sql_content.split(';'):
        statement = statement.strip()
        # Skip empty statements and comments
        if statement and not statement.startswith('--'):
            statements.append(statement)
    
    print(f"📊 Found {len(statements)} SQL statements to execute")
    print("⏳ Applying indexes (this may take a few minutes)...\n")
    
    executed = 0
    skipped = 0
    errors = 0
    
    async with engine.begin() as conn:
        for idx, statement in enumerate(statements, 1):
            # Extract operation name for logging
            first_line = statement.split('\n')[0][:80]
            
            try:
                await conn.execute(text(statement))
                executed += 1
                print(f"✅ [{idx}/{len(statements)}] {first_line}")
            except Exception as e:
                error_msg = str(e).lower()
                # If index already exists, that's okay
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    skipped += 1
                    print(f"⚠️  [{idx}/{len(statements)}] Already exists: {first_line}")
                else:
                    errors += 1
                    print(f"❌ [{idx}/{len(statements)}] Error: {first_line}")
                    print(f"   {str(e)[:200]}")
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Executed: {executed}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    print(f"{'='*60}\n")
    
    if errors == 0:
        print("✨ All indexes applied successfully!")
        print("💡 Restart your backend to use the optimizations")
        return 0
    else:
        print(f"⚠️  {errors} statement(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(apply_indexes())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
