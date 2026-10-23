"""
Saved / bookmarked jobs per user.
GET    /api/saved-jobs/         → list saved jobs (with full job details)
POST   /api/saved-jobs/{job_id} → bookmark a job
DELETE /api/saved-jobs/{job_id} → remove bookmark
"""

import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.models import SavedJob, Job as JobModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])


class SavedJobItem(BaseModel):
    """Response format matching what the frontend expects."""
    id: str           # saved_job record id
    job_id: str       # job id (used for unsave call)
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    apply_url: Optional[str] = None
    salary_range: Optional[str] = None
    saved_at: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/", response_model=List[SavedJobItem])
async def list_saved_jobs(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all jobs bookmarked by the current user, most recently saved first."""
    user_id = current_user["user_id"]
    result = await db.execute(
        select(SavedJob, JobModel)
        .join(JobModel, SavedJob.job_id == JobModel.id)
        .where(SavedJob.user_id == user_id)
        .order_by(SavedJob.saved_at.desc())
    )
    rows = result.all()
    out = []
    for saved, job in rows:
        out.append(SavedJobItem(
            id=str(saved.id),
            job_id=str(job.id),
            job_title=job.title,
            company_name=job.company_name,
            location=job.location,
            job_type=job.job_type,
            apply_url=job.apply_url,
            salary_range=job.salary_range,
            saved_at=saved.saved_at.isoformat() if saved.saved_at else None,
        ))
    return out


@router.post("/{job_id}", status_code=status.HTTP_201_CREATED)
async def save_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a job. Idempotent — saving the same job twice is safe."""
    user_id = current_user["user_id"]

    # Verify job exists
    job = await db.get(JobModel, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check already saved
    existing = await db.execute(
        select(SavedJob).where(
            and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        )
    )
    if existing.scalars().first():
        return {"msg": "Already saved", "job_id": job_id}

    saved = SavedJob(id=str(uuid.uuid4()), user_id=user_id, job_id=job_id)
    db.add(saved)
    await db.commit()
    return {"msg": "Job saved", "job_id": job_id}


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark. Returns 204 whether or not it existed."""
    user_id = current_user["user_id"]
    result = await db.execute(
        select(SavedJob).where(
            and_(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        )
    )
    saved = result.scalars().first()
    if saved:
        await db.delete(saved)
        await db.commit()
    return None
