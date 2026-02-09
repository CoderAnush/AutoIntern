from typing import AsyncGenerator
import aioredis
from app.core.config import settings

async def get_redis() -> AsyncGenerator:
    url = f"redis://{settings.redis_host}:{settings.redis_port}"
    client = aioredis.from_url(url)
    try:
        yield client
    finally:
        await client.close()
