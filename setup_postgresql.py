"""
PostgreSQL Database Setup Script

Creates database and user for CoinPulse.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def setup_postgresql():
    """Create PostgreSQL database and user."""

    print("=" * 60)
    print("PostgreSQL Setup for CoinPulse")
    print("=" * 60)

    # Database configuration
    db_name = 'coinpulse'
    db_user = 'coinpulse'
    db_password = 'coinpulse2024'

    try:
        # Connect to PostgreSQL as superuser (postgres)
        print("\n[1/4] Connecting to PostgreSQL...")
        print("Please enter the 'postgres' user password when prompted.")

        # Try to connect without password first (Windows authentication)
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                database='postgres'
            )
        except psycopg2.OperationalError:
            # If that fails, try with common default passwords
            passwords = ['postgres', '', 'admin', 'password']
            conn = None
            for pwd in passwords:
                try:
                    conn = psycopg2.connect(
                        host='localhost',
                        port=5432,
                        user='postgres',
                        password=pwd,
                        database='postgres'
                    )
                    break
                except psycopg2.OperationalError:
                    continue

            if conn is None:
                raise psycopg2.OperationalError("Could not connect with any default password")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("[OK] Connected to PostgreSQL")

        # Create user if not exists
        print(f"\n[2/4] Creating user '{db_user}'...")
        try:
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(db_user)
                ),
                [db_password]
            )
            print(f"[OK] User '{db_user}' created")
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                print(f"[INFO] User '{db_user}' already exists")
                # Update password
                cursor.execute(
                    sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                        sql.Identifier(db_user)
                    ),
                    [db_password]
                )
                print(f"[OK] Password updated for user '{db_user}'")
            else:
                raise

        # Create database if not exists
        print(f"\n[3/4] Creating database '{db_name}'...")
        try:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user)
                )
            )
            print(f"[OK] Database '{db_name}' created")
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                print(f"[INFO] Database '{db_name}' already exists")
                # Grant privileges
                cursor.execute(
                    sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                        sql.Identifier(db_name),
                        sql.Identifier(db_user)
                    )
                )
                print(f"[OK] Privileges granted to '{db_user}'")
            else:
                raise

        # Grant privileges
        print(f"\n[4/4] Granting privileges...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(db_user)
            )
        )
        print(f"[OK] All privileges granted to '{db_user}' on '{db_name}'")

        # Close connection
        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("PostgreSQL Setup Complete!")
        print("=" * 60)
        print(f"\nDatabase Configuration:")
        print(f"  Host: localhost")
        print(f"  Port: 5432")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        print(f"  Password: {db_password}")
        print(f"\nConnection String:")
        print(f"  postgresql://{db_user}:{db_password}@localhost:5432/{db_name}")
        print("\nNext Steps:")
        print("  1. Run: python init_database.py")
        print("  2. Start the servers")

        return True

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nPossible solutions:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Check if 'postgres' user password is correct")
        print("  3. Try running with correct postgres password")
        return False

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = setup_postgresql()
    sys.exit(0 if success else 1)
