import asyncio
import json
import pytest
pytest.importorskip('aioredis')
from app.db.session import AsyncSessionLocal
from processor import process_message
from worker import process_once, QUEUE_KEY, DLQ_KEY

REDIS_URL = "redis://localhost:6379"

@pytest.mark.asyncio
async def test_deduplication_inserts_once():
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
    except Exception:
        pytest.skip("Redis not available")

    payload = {"job": {"source": "test", "external_id": "dup-1", "title": "Dup Job", "location": "Remote"}}

    async with AsyncSessionLocal() as db:
        # ensure no existing
        await db.execute('DELETE FROM jobs WHERE external_id = :eid', {"eid": "dup-1"})
        await db.commit()

        job1 = await process_message(payload, db, elastic_url="http://localhost:9200")
        job2 = await process_message(payload, db, elastic_url="http://localhost:9200")
        assert job1.id == job2.id

        # cleanup
        await db.execute('DELETE FROM jobs WHERE external_id = :eid', {"eid": "dup-1"})
        await db.commit()

@pytest.mark.asyncio
async def test_dlq_after_retries():
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
    except Exception:
        pytest.skip("Redis not available")

    # push a message that will trigger a forced error in processor
    payload = {"job": {"source": "test", "external_id": "error-1", "title": "Err Job"}, "_test_force_error": True}
    await r.lpush(QUEUE_KEY, json.dumps(payload))

    # run process_once multiple times to simulate worker retries
    consumed = False
    for _ in range(5):
        consumed = await process_once(r)
        await asyncio.sleep(0.1)
        if not consumed:
            break

    # The message should end up in DLQ after retries
    dlq_item = await r.rpop(DLQ_KEY)
    assert dlq_item is not None
    msg = json.loads(dlq_item)
    assert msg.get('_error') is not None
    assert int(msg.get('_attempts', 0)) >= 1

    # cleanup DLQ
    await r.lpush(DLQ_KEY, json.dumps({'cleanup': True}))
    await r.rpop(DLQ_KEY)
