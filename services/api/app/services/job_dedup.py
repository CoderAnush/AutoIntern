"""Job deduplication and upsert logic."""

import uuid
import logging
from datetime import datetime
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Job as JobModel

logger = logging.getLogger(__name__)


async def upsert_jobs(db: AsyncSession, jobs: list[dict]) -> Tuple[int, int]:
    """
    Insert new jobs, skip duplicates.

    Deduplication uses:
      1. (source, external_id) pair — same job from same ATS
      2. dedupe_signature (MD5 of title+company+location) — catches cross-source dups

    Returns (inserted_count, skipped_count).
    """
    inserted = 0
    skipped = 0

    # Pre-load existing signatures and (source, external_id) pairs for fast lookup
    existing_sigs_result = await db.execute(
        select(JobModel.dedupe_signature).where(JobModel.dedupe_signature != None)
    )
    existing_sigs = set(existing_sigs_result.scalars().all())

    existing_ids_result = await db.execute(
        select(JobModel.source, JobModel.external_id)
        .where(JobModel.external_id != None)
    )
    existing_ids = {(r[0], r[1]) for r in existing_ids_result.all()}

    for job_data in jobs:
        source = job_data.get("source", "")
        ext_id = job_data.get("external_id", "")
        sig = job_data.get("dedupe_signature")

        # Check duplicates
        if ext_id and (source, ext_id) in existing_ids:
            skipped += 1
            continue
        if sig and sig in existing_sigs:
            skipped += 1
            continue

        # Parse posted_at
        posted_at = None
        if job_data.get("posted_at"):
            try:
                posted_at = datetime.fromisoformat(job_data["posted_at"])
            except Exception:
                posted_at = None

        new_job = JobModel(
            id=str(uuid.uuid4()),
            source=source,
            external_id=ext_id or None,
            title=job_data.get("title", "")[:512],
            description=job_data.get("description") or "",
            location=job_data.get("location") or "",
            company_name=job_data.get("company_name") or "",
            apply_url=job_data.get("apply_url") or "",
            salary_range=job_data.get("salary_range"),
            job_type=job_data.get("job_type") or "Full-time",
            posted_at=posted_at,
            dedupe_signature=sig,
            is_india_job=bool(job_data.get("is_india_job", False)),
        )
        db.add(new_job)

        # Track in local sets to avoid dups within same batch
        if sig:
            existing_sigs.add(sig)
        if ext_id:
            existing_ids.add((source, ext_id))

        inserted += 1

    if inserted:
        await db.commit()

    return inserted, skipped
