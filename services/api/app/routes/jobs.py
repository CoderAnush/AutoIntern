from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.job import JobCreate, JobOut
from app.db.session import get_db
from app.models.models import Job as JobModel
import uuid

router = APIRouter()

@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    new_id = str(uuid.uuid4())
    job = JobModel(
        id=new_id,
        source=payload.source,
        external_id=payload.external_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    # Increment metrics for jobs created (best-effort)
    try:
        from app.metrics import JOB_CREATE_COUNT

        JOB_CREATE_COUNT.inc()
    except Exception:
        pass
    return job

@router.get("/jobs", response_model=List[JobOut])
async def list_jobs(limit: int = 100, offset: int = 0, external_id: str | None = None, db: AsyncSession = Depends(get_db)):
    if external_id:
        q = await db.execute(select(JobModel).where(JobModel.external_id == external_id).limit(limit).offset(offset))
    else:
        q = await db.execute(select(JobModel).limit(limit).offset(offset))
    results = q.scalars().all()
    return results
