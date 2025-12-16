"""
Fix api_key column constraint in PostgreSQL
"""
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from backend.database.connection import init_database, get_db_session

print("="*60)
print("FIXING API_KEY CONSTRAINT IN POSTGRESQL")
print("="*60)

# Initialize database connection
engine = init_database(create_tables=False)

# Fix the constraint
try:
    with engine.connect() as conn:
        # Make api_key nullable
        print("\n[STEP 1] Altering api_key column to allow NULL...")
        conn.execute(text("ALTER TABLE users ALTER COLUMN api_key DROP NOT NULL"))
        conn.commit()
        print("[SUCCESS] api_key column is now nullable")

except Exception as e:
    print(f"[ERROR] {str(e)}")

print("\n" + "="*60)
print("FIX COMPLETE - Please test registration again")
print("="*60)
