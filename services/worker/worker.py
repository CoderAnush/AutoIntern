import asyncio
import os
import json
import aioredis
from app.db.session import AsyncSessionLocal
from app.db.session import engine
from app.core.config import settings
from processor import process_message

REDIS_URL = f"redis://{os.getenv('REDIS_HOST','redis')}:{os.getenv('REDIS_PORT',6379)}"
QUEUE_KEY = "ingest:jobs"
ELASTIC_URL = f"http://{os.getenv('ELASTIC_HOST','elasticsearch')}:{os.getenv('ELASTIC_PORT',9200)}"

async def process_once(redis):
    # One-off loop: BRPOP with timeout and process one message
    item = await redis.brpop(QUEUE_KEY, timeout=1)
    if not item:
        return False
    # item is (key, value)
    raw = item[1]
    try:
        message = json.loads(raw)
    except Exception:
        return False

    async with AsyncSessionLocal() as db:
        await process_message(message, db, elastic_url=ELASTIC_URL)
    return True

async def main():
    redis = aioredis.from_url(REDIS_URL)
    print(f"Worker connected to {REDIS_URL}, listening on {QUEUE_KEY}")
    try:
        while True:
            await process_once(redis)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        await redis.close()

if __name__ == '__main__':
    asyncio.run(main())
