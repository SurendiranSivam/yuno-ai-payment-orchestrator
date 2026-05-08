"""
Yuno AI Payment Operations Orchestrator — Database Module

Async SQLAlchemy engine and session factory.
Supports both PostgreSQL (production/Docker) and SQLite (local dev).
Tables are auto-created on application startup.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from config import get_settings

settings = get_settings()

# Detect database type
_is_sqlite = settings.database_url.startswith("sqlite")

# Engine configuration adapts to database type
_engine_kwargs: dict = {
    "echo": settings.debug,
}

if not _is_sqlite:
    # PostgreSQL connection pooling
    _engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# Session factory — expire_on_commit=False prevents DetachedInstanceError
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Create all tables on startup. Safe to call multiple times."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db():
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
