"""CLI utilities to inspect and requeue/delete DLQ items in Redis.

Usage:
  python scripts/dlq_cli.py list [count]
  python scripts/dlq_cli.py requeue <index>
  python scripts/dlq_cli.py delete <index>

This script expects REDIS_HOST/REDIS_PORT env vars (or defaults to redis:6379).
"""
import os
import sys
import json
import aioredis
import asyncio

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
DLQ_KEY = 'ingest:dlq'
QUEUE_KEY = 'ingest:jobs'

async def list_items(count=100):
    r = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    items = await r.lrange(DLQ_KEY, 0, count - 1)
    for i, raw in enumerate(items):
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode() if isinstance(raw, bytes) else str(raw)
        print(i, payload)
    await r.close()

async def requeue(index: int):
    r = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    raw = await r.lindex(DLQ_KEY, index)
    if not raw:
        print('item not found')
    else:
        await r.lrem(DLQ_KEY, 1, raw)
        await r.lpush(QUEUE_KEY, raw)
        print('requeued', index)
    await r.close()

async def delete(index: int):
    r = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    raw = await r.lindex(DLQ_KEY, index)
    if not raw:
        print('item not found')
    else:
        await r.lrem(DLQ_KEY, 1, raw)
        print('deleted', index)
    await r.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: list [count] | requeue <index> | delete <index>')
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'list':
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        asyncio.run(list_items(count))
    elif cmd == 'requeue' and len(sys.argv) == 3:
        asyncio.run(requeue(int(sys.argv[2])))
    elif cmd == 'delete' and len(sys.argv) == 3:
        asyncio.run(delete(int(sys.argv[2])))
    else:
        print('invalid args')
        sys.exit(1)
