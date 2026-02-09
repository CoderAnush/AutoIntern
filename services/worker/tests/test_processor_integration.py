import asyncio
import json
import time
import pytest
pytest.importorskip('aioredis')
from app.db.session import AsyncSessionLocal
from app.models.models import Job as JobModel
from processor import process_message

REDIS_URL = "redis://localhost:6379"
QUEUE_KEY = "ingest:jobs"

@pytest.mark.asyncio
async def test_process_message_inserts_job():
    # Ensure Redis is available
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
    except Exception:
        pytest.skip("Redis not available")

    # Create a sample message
    message = {"job": {"source": "test", "external_id": "ext123", "title": "Test Job", "description": "desc", "location": "Remote"}}

    # Process directly using DB session
    async with AsyncSessionLocal() as db:
        job = await process_message(message, db, elastic_url="http://localhost:9200")
        assert job.title == "Test Job"
        # Cleanup
        await db.delete(job)
        await db.commit()

@pytest.mark.asyncio
async def test_worker_consumes_from_redis_and_inserts():
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
    except Exception:
        pytest.skip("Redis not available")

    payload = {"job": {"source": "test-redis", "external_id": "ext-redis-1", "title": "Redis Job"}}
    await r.lpush(QUEUE_KEY, json.dumps(payload))

    # Run a single iteration to pick up the item
    # Using asyncio.run for subprocess-like isolation
    from worker import process_once

    consumed = await process_once(r)
    assert consumed is True

    # Verify DB
    async with AsyncSessionLocal() as db:
        q = await db.execute('SELECT * FROM jobs WHERE external_id = :eid', {"eid": "ext-redis-1"})
        rows = q.fetchall()
        assert len(rows) >= 1
        # cleanup
        await db.execute('DELETE FROM jobs WHERE external_id = :eid', {"eid": "ext-redis-1"})
        await db.commit()
