"""Async database engine and session factory for PostgreSQL.

This module configures the SQLAlchemy async engine and session factory for
database access. It provides the core database connectivity layer used by
FastAPI endpoints via dependency injection.

Configuration:
    - Pool size: 10 connections
    - Max overflow: 20 additional connections under load
    - expire_on_commit=False: Required for async sessions to prevent
      DetachedInstanceError when accessing lazy-loaded attributes

Environment Variables:
    DATABASE_URL: PostgreSQL connection string. Defaults to local development
        database if not set.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_database_url() -> str:
    """Get database URL from environment variable or use default.

    Returns:
        PostgreSQL connection string using asyncpg driver.
    """
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/pawarisk",
    )


# Create async engine at module import time (standard FastAPI pattern)
engine = create_async_engine(
    get_database_url(),
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Session factory with expire_on_commit=False (CRITICAL for async)
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose engine and close all connections.

    Call this in FastAPI shutdown event to avoid
    'Event loop is closed' warnings.
    """
    await engine.dispose()
