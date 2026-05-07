from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from app.core.config import settings

DATABASE_URL = settings.database_url

# Determine if using SQLite for local dev
is_sqlite = DATABASE_URL.startswith("sqlite")

# Synchronous engine for background tasks/scheduler
sync_url = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://") if is_sqlite else DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False} if is_sqlite else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Async engine configuration
engine_kwargs = {
    "echo": False,
    "future": True,
}

# SQLite requires special configuration for async
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool

engine: AsyncEngine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
