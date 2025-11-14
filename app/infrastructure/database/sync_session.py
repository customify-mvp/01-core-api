"""
Sync database session for Celery workers.

Celery doesn't support async operations natively, so we need a sync session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from app.config import settings
from app.infrastructure.database.session import Base


# Create sync engine for Celery workers
# Use the sync version of DATABASE_URL (without +asyncpg)
sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "")

sync_engine = create_engine(
    sync_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Sync session factory
SyncSessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_sync_db_session() -> Generator[Session, None, None]:
    """
    Context manager for sync database session (for Celery tasks).
    
    Usage:
        with get_sync_db_session() as session:
            user = session.query(User).first()
    
    Yields:
        Session: SQLAlchemy sync session
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
