import asyncio
import pytest
pytest.importorskip('aioredis')
from app.db.session import AsyncSessionLocal
from processor import process_message

REDIS_URL = "redis://localhost:6379"

@pytest.mark.asyncio
async def test_concurrent_inserts_dedup():
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
    except Exception:
        pytest.skip("Redis not available")

    payload = {"job": {"source": "test", "external_id": "concurrent-1", "title": "Concurrent Job", "location": "Remote"}}

    async with AsyncSessionLocal() as db:
        # cleanup before
        await db.execute('DELETE FROM jobs WHERE external_id = :eid', {"eid": "concurrent-1"})
        await db.commit()

    # Run two concurrent process_message calls
    async def run_one():
        async with AsyncSessionLocal() as db:
            return await process_message(payload, db, elastic_url="http://localhost:9200")

    res1, res2 = await asyncio.gather(run_one(), run_one())
    assert res1.id == res2.id

    async with AsyncSessionLocal() as db:
        # cleanup
        await db.execute('DELETE FROM jobs WHERE external_id = :eid', {"eid": "concurrent-1"})
        await db.commit()
