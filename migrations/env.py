"""
Alembic Environment Configuration for CoinPulse

This module configures Alembic to use CoinPulse database models and settings.
"""

from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv

from alembic import context

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ============================================================================
# Import CoinPulse Models
# ============================================================================

# Import Base and all models for autogenerate support
try:
    from backend.database.connection import Base
    from backend.database import models  # Import all models

    # Set target metadata
    target_metadata = Base.metadata

    print("[Alembic] Successfully imported CoinPulse models")
    print(f"[Alembic] Found {len(Base.metadata.tables)} tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

except Exception as e:
    print(f"[Alembic] ERROR importing models: {e}")
    import traceback
    traceback.print_exc()
    target_metadata = None


# ============================================================================
# Database URL Configuration
# ============================================================================

def get_database_url():
    """
    Get database URL from environment or default to SQLite.

    Priority:
    1. DATABASE_URL environment variable
    2. Default SQLite: sqlite:///data/coinpulse.db
    """
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Handle postgres:// URLs (Heroku/Railway format)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print(f"[Alembic] Using DATABASE_URL: {database_url}")
    else:
        # Default to SQLite
        database_url = 'sqlite:///data/coinpulse.db'
        print(f"[Alembic] Using default SQLite: {database_url}")

    return database_url


# ============================================================================
# Migration Functions
# ============================================================================

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database URL
    database_url = get_database_url()

    # Override config
    configuration = config.get_section(config.config_ini_section, {})
    configuration['sqlalchemy.url'] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
            render_as_batch=True,  # SQLite batch mode for ALTER operations
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
