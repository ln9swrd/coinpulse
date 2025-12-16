"""
Quick Database Initialization using SQLAlchemy
Creates all tables defined in models
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.database.connection import Base, init_database
from backend.database.models import (
    User, Session, EmailVerification, PasswordReset, UserAPIKey,
    UserConfig, SwingPosition, SwingPositionHistory, SwingTradingLog,
    Order, HoldingsHistory, PriceCache, TradingSignal,
    StrategyPerformance, SyncStatus, SystemLog
)

def create_all_tables():
    """Create all tables using SQLAlchemy"""
    try:
        print("=" * 60)
        print("  Creating All Tables")
        print("=" * 60)
        
        # Initialize database first
        engine = init_database(create_tables=False)
        print(f"Database URL: {engine.url}")
        print()
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("SUCCESS: All tables created!")
        print()
        
        # List created tables
        print("Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        
        print()
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_all_tables()
    sys.exit(0 if success else 1)
