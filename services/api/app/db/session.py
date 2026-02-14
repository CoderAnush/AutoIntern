from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings

DATABASE_URL = settings.database_url

# Determine if using SQLite for local dev
is_sqlite = DATABASE_URL.startswith("sqlite")

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

# Alias for compatibility
SessionLocal = AsyncSessionLocal

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
