"""
Database Connection Module

Manages PostgreSQL/SQLite database connections using SQLAlchemy.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Base class for all models
Base = declarative_base()

# Global engine and session factory
engine = None
SessionFactory = None


def get_database_url():
    """
    Get database URL from environment variables.

    Priority:
    1. DATABASE_URL environment variable (complete URL)
    2. Individual DB_* variables (DB_TYPE, DB_HOST, etc.)
    3. Fallback to SQLite (development)

    Returns:
        str: Database connection URL
    """
    # Load .env file first
    load_dotenv()

    # Check for complete DATABASE_URL first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"[Database] Using DATABASE_URL: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
        return db_url

    # Check DB_TYPE to determine which database to use
    db_type = os.getenv('DB_TYPE', 'sqlite').lower()

    if db_type == 'postgresql':
        # Build PostgreSQL URL from individual variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'coinpulse')

        # Construct PostgreSQL URL
        db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        print(f"[Database] Using PostgreSQL: {db_host}:{db_port}/{db_name}")
        return db_url

    # Fallback to SQLite (development)
    sqlite_path = os.getenv('DB_SQLITE_PATH', os.path.join('data', 'coinpulse.db'))
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    print(f"[Database] Using SQLite: {sqlite_path}")
    return f'sqlite:///{sqlite_path}'


def init_database(create_tables=True):
    """
    Initialize database connection and create tables.

    Args:
        create_tables (bool): Whether to create tables if they don't exist

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global engine, SessionFactory

    # Load database settings from environment variables
    pool_size = int(os.getenv('DB_POOL_SIZE', 50))
    max_overflow = int(os.getenv('DB_MAX_OVERFLOW', 50))
    pool_recycle = int(os.getenv('DB_POOL_RECYCLE', 3600))
    pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', 30))
    pool_pre_ping = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'
    echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
    autocommit = os.getenv('DB_AUTOCOMMIT', 'false').lower() == 'true'
    autoflush = os.getenv('DB_AUTOFLUSH', 'false').lower() == 'true'
    expire_on_commit = os.getenv('DB_EXPIRE_ON_COMMIT', 'false').lower() == 'true'

    db_url = get_database_url()

    # Create engine
    if db_url.startswith('sqlite'):
        # SQLite specific settings
        engine = create_engine(
            db_url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            echo=echo
        )
        print(f"[Database] SQLite engine created (echo={echo})")
    else:
        # PostgreSQL settings - from config file
        engine = create_engine(
            db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
            pool_timeout=pool_timeout,
            echo=echo
        )
        print(f"[Database] PostgreSQL engine created:")
        print(f"  - pool_size: {pool_size}")
        print(f"  - max_overflow: {max_overflow} (total: {pool_size + max_overflow})")
        print(f"  - pool_recycle: {pool_recycle}s")
        print(f"  - pool_timeout: {pool_timeout}s")

    # Create session factory - thread-safe with scoped_session
    SessionFactory = scoped_session(sessionmaker(
        bind=engine,
        autocommit=autocommit,
        autoflush=autoflush,
        expire_on_commit=expire_on_commit
    ))
    print(f"[Database] Session factory created (autocommit={autocommit}, autoflush={autoflush}, expire_on_commit={expire_on_commit})")

    # Create tables if requested
    if create_tables:
        print("[Database] Creating tables...")
        from . import models  # Import models to register them
        try:
            Base.metadata.create_all(bind=engine)
            print("[Database] Tables created successfully")
        except Exception as e:
            # Ignore duplicate table/index errors (they already exist)
            if "already exists" in str(e) or "DuplicateTable" in str(e) or "이미 존재" in str(e):
                print(f"[Database] Tables/indexes already exist (ignored): {str(e)[:100]}")
            else:
                print(f"[Database] Warning: Table creation error: {str(e)}")
                # Don't raise - allow the application to continue

    print("[Database] Database initialized successfully")
    return engine


def get_db_session():
    """
    Get a database session.

    Usage:
        session = get_db_session()
        try:
            # Use session
            session.add(obj)
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    Returns:
        Session: SQLAlchemy session instance
    """
    global SessionFactory

    if SessionFactory is None:
        init_database()

    return SessionFactory()


def get_db():
    """
    Get database session generator for FastAPI/Flask dependency injection.
    
    Usage in Flask routes:
        db = next(get_db())
        try:
            # Use db
        finally:
            db.close()
    
    Yields:
        Session: SQLAlchemy session instance
    """
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


def close_database():
    """Close database connections and clean up resources."""
    global engine, SessionFactory

    if SessionFactory:
        SessionFactory.remove()
        SessionFactory = None

    if engine:
        engine.dispose()
        engine = None

    print("[Database] Database connections closed")
