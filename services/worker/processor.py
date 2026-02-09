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

async def process_message(message: Dict[str, Any], db: AsyncSession, elastic_url: str = "http://elasticsearch:9200") -> JobModel:
    # Normalize message and insert into DB
    payload = message.get("job") if isinstance(message, dict) else message
    job = JobModel(
        id=message.get("id") if message.get("id") else None,
        source=payload.get("source"),
        external_id=payload.get("external_id"),
        title=payload.get("title"),
        description=payload.get("description"),
        location=payload.get("location"),
        raw=payload.get("raw", {}),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Index to ES (best-effort)
    await index_to_elasticsearch(job, elastic_url)

    return job
