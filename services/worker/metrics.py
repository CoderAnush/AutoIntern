from prometheus_client import Counter, Gauge, start_http_server
import asyncio
import os

PROCESSED = Counter("worker_processed_total", "Total messages processed", ["result"])
DLQ_GAUGE = Gauge("worker_dlq_size", "Size of the DLQ list in Redis")

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DLQ_KEY = 'ingest:dlq'

async def update_dlq_size(redis_client):
    try:
        size = await redis_client.llen(DLQ_KEY)
        DLQ_GAUGE.set(size)
    except Exception:
        pass

def start_metrics_server(port: int = 8001):
    # Start Prometheus HTTP server in background thread
    start_http_server(port)

async def metrics_loop(redis_client):
    while True:
        await update_dlq_size(redis_client)
        await asyncio.sleep(5)
