import json
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Job as JobModel
import httpx

async def index_to_elasticsearch(job: JobModel, elastic_url: str):
    # Placeholder: simple HTTP index request to Elasticsearch
    async with httpx.AsyncClient() as client:
        try:
            doc = {
                "id": str(job.id),
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "source": job.source,
            }
            # Using a simple index API; in production use official client and index settings
            await client.post(f"{elastic_url}/autointern-jobs/_doc/{job.id}", json=doc, timeout=5.0)
        except Exception:
            # Fail silently for now; in prod, add retries and logging
            pass

from utils import make_dedupe_signature

async def process_message(message: Dict[str, Any], db: AsyncSession, elastic_url: str = "http://elasticsearch:9200") -> JobModel:
    # Normalize message and insert into DB with deduplication and idempotency
    payload = message.get("job") if isinstance(message, dict) else message

    # Support a test-only flag to force an error for retry/DLQ testing
    if payload.get("_test_force_error"):
        raise RuntimeError("forced error for test")

    signature = make_dedupe_signature(payload)

    # Check for existing job by external_id or dedupe_signature
    if payload.get("external_id"):
        q = await db.execute(
            "SELECT * FROM jobs WHERE external_id = :eid LIMIT 1",
            {"eid": payload.get("external_id")},
        )
        row = q.fetchone()
        if row:
            # Return existing job object
            existing = await db.get(JobModel, row.id)
            return existing

    q2 = await db.execute(
        "SELECT * FROM jobs WHERE dedupe_signature = :sig LIMIT 1",
        {"sig": signature},
    )
    row2 = q2.fetchone()
    if row2:
        existing = await db.get(JobModel, row2.id)
        return existing

    # Insert new job
    job = JobModel(
        id=message.get("id") if message.get("id") else None,
        source=payload.get("source"),
        external_id=payload.get("external_id"),
        title=payload.get("title"),
        description=payload.get("description"),
        location=payload.get("location"),
        raw=payload.get("raw", {}),
        dedupe_signature=signature,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Index to ES (best-effort)
    await index_to_elasticsearch(job, elastic_url)

    return job
