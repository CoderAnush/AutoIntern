import argparse
import json
import os
import aioredis
import asyncio

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DLQ_KEY = 'ingest:dlq'

async def push(payload: str):
    r = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    await r.lpush(DLQ_KEY, payload)
    await r.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--payload', required=True)
    args = p.parse_args()
    asyncio.run(push(args.payload))
