"""
Database session management.

Provides async SQLAlchemy engine, session factory, and Base for models.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool

from app.config import settings


# SQLAlchemy 2.0 Base class
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine with optimized pooling
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    poolclass=QueuePool,  # Explicitly use QueuePool (default for non-SQLite)
    pool_size=20,  # Max connections in pool
    max_overflow=10,  # Max extra connections when pool exhausted
    pool_pre_ping=True,  # Verify connection before using (catches stale connections)
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
    pool_timeout=30,  # Wait 30s for connection from pool before error
    pool_reset_on_return='rollback',  # Reset connection state on return to pool
    connect_args={
        "server_settings": {"jit": "off"},  # Disable JIT compilation for faster connections
        "command_timeout": 60,  # Query timeout (60 seconds)
        "prepared_statement_cache_size": 500,  # Cache prepared statements for performance
    } if 'postgresql' in str(settings.DATABASE_URL) else {},
    # Use NullPool for serverless (AWS Lambda) - uncomment if needed
    # poolclass=NullPool,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @router.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database (create tables).
    
    NOTE: Only use this in development.
    In production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()