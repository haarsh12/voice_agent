import sqlite3
import os

db_path = "d:/voice_stream/backend/sahayak-dev.db"

sql_sqlite = """
DELETE FROM sahayak_grievance_events;
DELETE FROM sahayak_grievances;
DELETE FROM sahayak_webauthn_credentials;
DELETE FROM sahayak_webauthn_ceremonies;
DELETE FROM sahayak_otp_codes;
DELETE FROM sahayak_accounts;
"""

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.executescript(sql_sqlite)
    
    # Try adding columns. If they exist, this will throw an error, we catch it.
    try:
        cursor.execute("ALTER TABLE sahayak_accounts ADD COLUMN pincode varchar(10);")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE sahayak_accounts ADD COLUMN caste_category varchar(32);")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    print("Migration successful")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
