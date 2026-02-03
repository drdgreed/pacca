"""
Database session management and connection handling.

Provides async database session management using SQLAlchemy 2.0
with connection pooling and proper lifecycle management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from pacca.config import get_logger, get_settings

logger = get_logger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine.

    Returns:
        AsyncEngine instance configured for the application
    """
    global _engine

    if _engine is None:
        settings = get_settings()

        # Determine if using SQLite (for local dev) or PostgreSQL
        is_sqlite = settings.database_url.startswith("sqlite")

        engine_kwargs = {
            "echo": settings.debug and settings.log_level == "DEBUG",
        }

        # PostgreSQL-specific settings
        if not is_sqlite:
            engine_kwargs.update(
                {
                    "pool_size": settings.db_pool_size,
                    "max_overflow": settings.db_max_overflow,
                    "pool_timeout": settings.db_pool_timeout,
                    "pool_pre_ping": True,  # Check connection health
                }
            )

        _engine = create_async_engine(settings.database_url, **engine_kwargs)

        logger.info(
            "database_engine_created",
            database_type="sqlite" if is_sqlite else "postgresql",
            pool_size=settings.db_pool_size if not is_sqlite else "N/A",
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the session factory.

    Returns:
        Session factory for creating database sessions
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.

    Yields:
        AsyncSession for database operations

    Usage:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Usage:
        async with get_session_context() as session:
            result = await session.execute(query)
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database() -> None:
    """
    Initialize the database, creating all tables.

    Should be called during application startup.
    """
    from pacca.db.models import Base

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_initialized")


async def close_database() -> None:
    """
    Close database connections.

    Should be called during application shutdown.
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None

    logger.info("database_connections_closed")


async def health_check() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        async with get_session_context() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False
