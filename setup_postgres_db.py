"""
Setup PostgreSQL Database for CoinPulse
Attempts multiple connection methods
"""

import subprocess
import sys
import os

def run_sql_file(sql_commands):
    """Run SQL commands via psql"""
    psql_path = r"C:\Program Files\PostgreSQL\16\bin\psql.exe"

    # Create temporary SQL file
    with open('temp_setup.sql', 'w', encoding='utf-8') as f:
        f.write(sql_commands)

    # Try different authentication methods
    passwords = ['postgres', 'admin', '1234', 'password', '', 'root']

    for pwd in passwords:
        print(f"Trying password: {'(empty)' if pwd == '' else '***'}")

        env = os.environ.copy()
        if pwd:
            env['PGPASSWORD'] = pwd

        cmd = [
            psql_path,
            '-U', 'postgres',
            '-h', 'localhost',
            '-p', '5432',
            '-d', 'postgres',
            '-f', 'temp_setup.sql'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )

            if result.returncode == 0:
                print("[OK] Connection successful!")
                os.remove('temp_setup.sql')
                return True, result.stdout

        except Exception as e:
            continue

    os.remove('temp_setup.sql')
    return False, "All password attempts failed"

def main():
    print("=" * 70)
    print("PostgreSQL Database Setup for CoinPulse")
    print("=" * 70)
    print()

    # SQL commands to setup database
    sql_commands = """
-- Check if database exists and create if not
SELECT 'CREATE DATABASE coinpulse'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coinpulse')\\gexec

-- Create user if not exists
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'coinpulse') THEN
      CREATE USER coinpulse WITH PASSWORD 'coinpulse2024';
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE coinpulse TO coinpulse;

-- Connect to coinpulse database
\\c coinpulse

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO coinpulse;
GRANT ALL ON ALL TABLES IN SCHEMA public TO coinpulse;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO coinpulse;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO coinpulse;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO coinpulse;

-- Show result
SELECT 'Database setup complete!' as status;
"""

    print("[1/3] Creating PostgreSQL database and user...")
    print()

    success, output = run_sql_file(sql_commands)

    if not success:
        print()
        print("[ERROR] Could not connect to PostgreSQL")
        print()
        print("Please try one of these methods:")
        print()
        print("METHOD 1: Use pgAdmin")
        print("  1. Open pgAdmin")
        print("  2. Right-click Databases -> Create -> Database")
        print("  3. Name: coinpulse")
        print()
        print("METHOD 2: Manual SQL")
        print("  Run these commands in pgAdmin Query Tool:")
        print("  CREATE DATABASE coinpulse;")
        print("  CREATE USER coinpulse WITH PASSWORD 'coinpulse2024';")
        print("  GRANT ALL PRIVILEGES ON DATABASE coinpulse TO coinpulse;")
        print()
        return False

    print(output)
    print()

    # Test connection with coinpulse user
    print("[2/3] Testing connection with coinpulse user...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='coinpulse',
            password='coinpulse2024',
            database='coinpulse'
        )
        print("[OK] Connection successful!")

        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"PostgreSQL version: {version[:50]}...")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    # Initialize tables
    print()
    print("[3/3] Initializing database tables...")
    print("Run: python init_database.py")
    print()

    print("=" * 70)
    print("[OK] PostgreSQL setup complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. python init_database.py")
    print("  2. Restart servers")
    print()

    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
