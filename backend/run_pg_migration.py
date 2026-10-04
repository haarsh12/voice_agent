import asyncio
import asyncpg
import os

DATABASE_URL = "postgresql://postgres:ShantiNagar12@db.rrmzhdnawsuxjcdtxwqm.supabase.co:5432/postgres"

sql = """
-- Drop all rows
DELETE FROM sahayak_grievance_events;
DELETE FROM sahayak_grievances;
DELETE FROM sahayak_webauthn_credentials;
DELETE FROM sahayak_webauthn_ceremonies;
DELETE FROM sahayak_otp_codes;
DELETE FROM sahayak_accounts;

-- Restart sequences
ALTER SEQUENCE sahayak_accounts_id_seq RESTART WITH 1;
ALTER SEQUENCE sahayak_otp_codes_id_seq RESTART WITH 1;
ALTER SEQUENCE sahayak_grievance_events_id_seq RESTART WITH 1;

-- Add new columns safely
ALTER TABLE sahayak_accounts ADD COLUMN IF NOT EXISTS pincode VARCHAR(10);
ALTER TABLE sahayak_accounts ADD COLUMN IF NOT EXISTS caste_category VARCHAR(32);
"""

async def run_migration():
    print("Connecting to Supabase PostgreSQL...")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("Executing migration...")
        await conn.execute(sql)
        print("Migration applied successfully!")
    except Exception as e:
        print(f"Error executing migration: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
