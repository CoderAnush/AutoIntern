from typing import AsyncGenerator, Optional
from app.core.config import settings


async def get_redis() -> AsyncGenerator:
    """Yield a Redis client if Redis is configured; yield None otherwise."""
    redis_url = getattr(settings, "redis_url", "") or ""
    if not redis_url:
        yield None
        return
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(redis_url)
        try:
            yield client
        finally:
            await client.aclose()
    except ImportError:
        yield None
