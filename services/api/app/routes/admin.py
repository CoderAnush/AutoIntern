from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
import json
from app.deps.redis import get_redis
from app.core.config import settings

router = APIRouter()
DLQ_KEY = "ingest:dlq"
QUEUE_KEY = "ingest:jobs"

async def require_admin(x_admin_token: Optional[str] = Header(None)):
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin API not configured")
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin token")

@router.get("/admin/dlq", dependencies=[Depends(require_admin)])
async def list_dlq(count: int = 100, redis=Depends(get_redis)):
    # Return up to `count` items from DLQ (most recent first)
    items = await redis.lrange(DLQ_KEY, 0, count - 1)
    parsed = []
    for i, raw in enumerate(items):
        try:
            parsed.append({"index": i, "payload": json.loads(raw)})
        except Exception:
            parsed.append({"index": i, "payload": raw.decode() if isinstance(raw, bytes) else str(raw)})
    return {"count": len(parsed), "items": parsed}

class RequeueRequest(BaseModel := object):
    # Lightweight placeholder to keep type hints simple without adding more deps
    index: int

@router.post("/admin/dlq/requeue", dependencies=[Depends(require_admin)])
async def requeue_item(body: dict, redis=Depends(get_redis)):
    index = body.get("index")
    if index is None:
        raise HTTPException(status_code=400, detail="index is required")
    raw = await redis.lindex(DLQ_KEY, index)
    if not raw:
        raise HTTPException(status_code=404, detail="item not found")
    # Remove the item (first occurrence) and push to queue
    await redis.lrem(DLQ_KEY, 1, raw)
    await redis.lpush(QUEUE_KEY, raw)
    return {"status": "requeued", "index": index}

@router.delete("/admin/dlq", dependencies=[Depends(require_admin)])
async def delete_item(index: int, redis=Depends(get_redis)):
    raw = await redis.lindex(DLQ_KEY, index)
    if not raw:
        raise HTTPException(status_code=404, detail="item not found")
    await redis.lrem(DLQ_KEY, 1, raw)
    return {"status": "deleted", "index": index}
