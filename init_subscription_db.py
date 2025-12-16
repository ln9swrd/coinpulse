"""
Initialize Subscription Database
Creates subscription and transaction tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.subscription_models import Base, Subscription, Transaction

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Default to SQLite if no DATABASE_URL
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///data/coinpulse.db'
    print(f"[Database] Using SQLite: {DATABASE_URL}")
elif DATABASE_URL.startswith('postgres://'):
    # Heroku/Railway uses postgres://, but SQLAlchemy requires postgresql://
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print(f"[Database] Using PostgreSQL (converted URL)")


def init_database():
    """Initialize the subscription database"""
    print("=" * 70)
    print("COINPULSE SUBSCRIPTION DATABASE INITIALIZATION")
    print("=" * 70)
    print()

    try:
        # Create engine
        if DATABASE_URL.startswith('sqlite'):
            # SQLite
            engine = create_engine(DATABASE_URL, echo=False)
            print(f"[Database] SQLite engine created")
        else:
            # PostgreSQL
            engine = create_engine(
                DATABASE_URL,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            print(f"[Database] PostgreSQL engine created")
            print(f"  - pool_size: 10")
            print(f"  - max_overflow: 20 (total: 30)")
            print(f"  - pool_recycle: 3600s")

        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
        print(f"[Database] Session factory created")

        # Create tables
        print()
        print("[1/2] Creating subscription tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created successfully")

        # Verify tables exist
        print()
        print("[2/2] Verifying tables...")
        with engine.connect() as conn:
            if DATABASE_URL.startswith('sqlite'):
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('subscriptions', 'transactions')"
                ))
            else:
                result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('subscriptions', 'transactions')"
                ))

            tables = [row[0] for row in result]
            print(f"[Database] Found tables: {', '.join(tables)}")

            if 'subscriptions' in tables and 'transactions' in tables:
                print("[OK] All tables verified")
            else:
                print("[WARNING] Some tables missing!")
                return False

        print()
        print("=" * 70)
        print("SUBSCRIPTION DATABASE INITIALIZED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Tables created:")
        print("  - subscriptions (user subscriptions)")
        print("  - transactions (payment transactions)")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR: Failed to initialize subscription database")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
