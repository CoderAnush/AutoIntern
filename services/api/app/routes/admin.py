from fastapi import APIRouter, BackgroundTasks, status, HTTPException, Depends, Header
from typing import Optional
import json
from pydantic import BaseModel
from sqlalchemy import select
import logging
from app.db.session import AsyncSessionLocal
from app.services.embeddings_service import EmbeddingsManager
from app.models.models import Job, Resume
from app.deps.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

DLQ_KEY = "ingest:dlq"
QUEUE_KEY = "ingest:jobs"

async def require_admin(x_admin_token: Optional[str] = Header(None)):
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin API not configured")
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin token")

@router.get("/dlq", dependencies=[Depends(require_admin)])
async def list_dlq(count: int = 100, redis=Depends(get_redis)):
    items = await redis.lrange(DLQ_KEY, 0, count - 1)
    parsed = []
    for i, raw in enumerate(items):
        try:
            parsed.append({"index": i, "payload": json.loads(raw)})
        except Exception:
            parsed.append({"index": i, "payload": raw.decode() if isinstance(raw, bytes) else str(raw)})
    return {"count": len(parsed), "items": parsed}

class RequeueRequest(BaseModel):
    index: int

@router.post("/dlq/requeue", dependencies=[Depends(require_admin)])      
async def requeue_item(body: RequeueRequest, redis=Depends(get_redis)):        
    index = body.index
    if index is None:
        raise HTTPException(status_code=400, detail="index is required")       
    raw = await redis.lindex(DLQ_KEY, index)
    if not raw:
        raise HTTPException(status_code=404, detail="item not found")
    await redis.lrem(DLQ_KEY, 1, raw)
    await redis.lpush(QUEUE_KEY, raw)
    return {"status": "requeued", "index": index}

@router.delete("/dlq", dependencies=[Depends(require_admin)])
async def delete_item(index: int, redis=Depends(get_redis)):
    raw = await redis.lindex(DLQ_KEY, index)
    if not raw:
        raise HTTPException(status_code=404, detail="item not found")
    await redis.lrem(DLQ_KEY, 1, raw)
    return {"status": "deleted", "index": index}


@router.post("/generate-embeddings", status_code=status.HTTP_202_ACCEPTED)
async def trigger_embeddings_generation(
    background_tasks: BackgroundTasks,
):
    """
    Trigger background generation of embeddings for all jobs and resumes.
    """
    background_tasks.add_task(generate_embeddings_task)
    return {"message": "Embeddings generation started in background"}


async def generate_embeddings_task():
    """Background task to generate embeddings."""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting background embeddings generation...")
            embeddings_mgr = EmbeddingsManager()

            # Process Jobs
            result = await db.execute(select(Job))
            jobs = result.scalars().all()
            job_count = 0

            for job in jobs:
                try:
                    if job.description and len(job.description) > 20:
                        await embeddings_mgr.add_job_embedding(job.id, job.description, db)
                        job_count += 1
                except Exception as e:
                    logger.error(f"Failed to process job {job.id}: {e}")

            # Process Resumes
            result = await db.execute(select(Resume))
            resumes = result.scalars().all()
            resume_count = 0

            for resume in resumes:
                try:
                    if resume.parsed_text and len(resume.parsed_text) > 20:
                        await embeddings_mgr.add_resume_embedding(resume.id, resume.parsed_text, db)
                        resume_count += 1
                except Exception as e:
                    logger.error(f"Failed to process resume {resume.id}: {e}")

            logger.info(f"Embeddings generation complete. Processed {job_count} jobs and {resume_count} resumes.")

        except Exception as e:
            logger.error(f"Global error in embeddings generation task: {e}")
