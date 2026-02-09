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
DLQ_KEY = "ingest:dlq"
ELASTIC_URL = f"http://{os.getenv('ELASTIC_HOST','elasticsearch')}:{os.getenv('ELASTIC_PORT',9200)}"
MAX_RETRIES = int(os.getenv('WORKER_MAX_RETRIES', 3))

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
        # Could not parse JSON, move directly to DLQ with raw content
        await redis.lpush(DLQ_KEY, raw)
        return True

    # Track attempts for retry logic
    attempts = int(message.get("_attempts", 0))

    try:
        async with AsyncSessionLocal() as db:
            await process_message(message, db, elastic_url=ELASTIC_URL)
        return True
    except Exception as exc:
        attempts += 1
        if attempts >= MAX_RETRIES:
            # Move to DLQ with error info
            message['_error'] = str(exc)
            message['_attempts'] = attempts
            await redis.lpush(DLQ_KEY, json.dumps(message))
            return True
        else:
            # Requeue for retry with updated attempt count
            message['_attempts'] = attempts
            await redis.lpush(QUEUE_KEY, json.dumps(message))
            return True

async def main():
    redis = aioredis.from_url(REDIS_URL)
    print(f"Worker connected to {REDIS_URL}, listening on {QUEUE_KEY}")

    # Start Prometheus metrics server and a coroutine to update DLQ gauge
    try:
        from metrics import start_metrics_server, metrics_loop
        start_metrics_server(port=int(os.getenv('WORKER_METRICS_PORT', 8001)))
        asyncio.create_task(metrics_loop(redis))
    except Exception:
        pass

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
