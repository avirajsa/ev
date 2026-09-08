import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.models import Base

logger = logging.getLogger("ev.db")

# Async SQLAlchemy Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=10,
    max_overflow=20
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for producing async DB sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initializes PostgreSQL database:
    1. Enables pgvector extension (`CREATE EXTENSION IF NOT EXISTS vector;`)
    2. Creates all tables defined in Base metadata.
    """
    logger.info("[Database] Initializing PostgreSQL database and Pgvector extension...")
    try:
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[Database] PostgreSQL database and Pgvector extension initialized successfully.")
    except Exception as e:
        logger.warning(f"[Database] Could not auto-initialize DB (PostgreSQL might be offline): {e}")
