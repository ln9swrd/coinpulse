"""
Database Package

Provides database connection, models, and ORM functionality.
"""

from .connection import get_db_session, init_database, engine, Base
from .models import (
    Order, HoldingsHistory, PriceCache, TradingSignal, StrategyPerformance, SyncStatus, SystemLog,
    User, UserConfig, SwingPosition, SwingPositionHistory, SwingTradingLog
)

__all__ = [
    'get_db_session',
    'init_database',
    'engine',
    'Base',
    # Holdings tracking models
    'Order',
    'HoldingsHistory',
    'PriceCache',
    'TradingSignal',
    'StrategyPerformance',
    'SyncStatus',
    'SystemLog',
    # Swing trading multi-user models
    'User',
    'UserConfig',
    'SwingPosition',
    'SwingPositionHistory',
    'SwingTradingLog'
]
