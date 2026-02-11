import json
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Job as JobModel
import httpx

INDEX_NAME = "autointern-jobs"
INDEX_TEMPLATE = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "external_id": {"type": "keyword"},
            "title": {"type": "text"},
            "description": {"type": "text"},
            "location": {"type": "keyword"},
            "source": {"type": "keyword"},
        }
    },
}

_INDEX_READY = False


async def ensure_index(client: httpx.AsyncClient, elastic_url: str) -> None:
    global _INDEX_READY
    if _INDEX_READY:
        return
    try:
        head = await client.head(f"{elastic_url}/{INDEX_NAME}", timeout=5.0)
        if head.status_code == 404:
            resp = await client.put(f"{elastic_url}/{INDEX_NAME}", json=INDEX_TEMPLATE, timeout=10.0)
            if resp.status_code not in (200, 201):
                print(f"ES index create failed: {resp.status_code} - {resp.text}")
        _INDEX_READY = True
    except Exception as exc:
        print(f"ES ensure index error: {exc}")

async def index_to_elasticsearch(job: JobModel, elastic_url: str):
    # Robust HTTP index request to Elasticsearch with basic error handling
    async with httpx.AsyncClient() as client:
        try:
            await ensure_index(client, elastic_url)
            doc = {
                "id": str(job.id),
                "external_id": job.external_id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "source": job.source,
            }
            # Using a simple index API; in production use official client and index settings
            headers = {"Content-Type": "application/json"}
            resp = await client.post(f"{elastic_url}/{INDEX_NAME}/_doc/{job.id}", json=doc, headers=headers, timeout=5.0)
            if resp.status_code not in (200, 201):
                # Basic logging for visibility; in production use structured logging and retries
                print(f"ES index failed: {resp.status_code} - {resp.text}")
        except Exception as exc:
            # Fail silently for now but print for local debugging; in prod, add retries and monitoring
            print(f"ES index error: {exc}")
            pass

from utils import make_dedupe_signature

import uuid
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


async def process_message(message: Dict[str, Any], db: AsyncSession, elastic_url: str = "http://elasticsearch:9200") -> JobModel:
    # Normalize message and insert into DB with deduplication and idempotency using DB constraints
    payload = message.get("job") if isinstance(message, dict) else message

    # Support a test-only flag to force an error for retry/DLQ testing
    if payload.get("_test_force_error"):
        raise RuntimeError("forced error for test")

    signature = make_dedupe_signature(payload)

    job_id = message.get("id") if message.get("id") else str(uuid.uuid4())

    # Try an upsert on dedupe_signature; handle external_id unique constraint gracefully
    insert_sql = text(
        """
        INSERT INTO jobs (id, source, external_id, title, description, location, raw, dedupe_signature)
        VALUES (:id, :source, :external_id, :title, :description, :location, :raw::jsonb, :dedupe_signature)
        ON CONFLICT (dedupe_signature) DO UPDATE SET
          external_id = COALESCE(jobs.external_id, EXCLUDED.external_id),
          title = COALESCE(jobs.title, EXCLUDED.title),
          description = COALESCE(jobs.description, EXCLUDED.description),
          location = COALESCE(jobs.location, EXCLUDED.location)
        RETURNING id
        """
    )

    params = {
        "id": job_id,
        "source": payload.get("source"),
        "external_id": payload.get("external_id"),
        "title": payload.get("title"),
        "description": payload.get("description"),
        "location": payload.get("location"),
        "raw": payload.get("raw", {}),
        "dedupe_signature": signature,
    }

    try:
        result = await db.execute(insert_sql, params)
        await db.commit()
        row = result.fetchone()
        if row and row[0]:
            inserted_id = row[0]
            job = await db.get(JobModel, inserted_id)
            # Index to ES (best-effort)
            await index_to_elasticsearch(job, elastic_url)
            return job
    except IntegrityError as ie:
        # Could be unique violation on external_id; try to find existing by external_id
        await db.rollback()
        if payload.get("external_id"):
            q = await db.execute(
                "SELECT id FROM jobs WHERE external_id = :eid LIMIT 1",
                {"eid": payload.get("external_id")},
            )
            r = q.fetchone()
            if r:
                job = await db.get(JobModel, r[0])
                return job
        # If not found, re-raise
        raise

    # Fallback: if insert did not return row, try to find by signature or external_id
    q2 = await db.execute(
        "SELECT id FROM jobs WHERE dedupe_signature = :sig LIMIT 1",
        {"sig": signature},
    )
    r2 = q2.fetchone()
    if r2:
        return await db.get(JobModel, r2[0])

    if payload.get("external_id"):
        q3 = await db.execute(
            "SELECT id FROM jobs WHERE external_id = :eid LIMIT 1",
            {"eid": payload.get("external_id")},
        )
        r3 = q3.fetchone()
        if r3:
            return await db.get(JobModel, r3[0])

    # Final fallback: create via ORM (should be rare)
    job = JobModel(
        id=job_id,
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
    await index_to_elasticsearch(job, elastic_url)
    return job
