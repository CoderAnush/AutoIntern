from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.schemas.job import JobCreate, JobOut
from app.db.session import get_db
from app.models.models import Job as JobModel, Embedding as EmbeddingModel
from app.services.embeddings_service import EmbeddingsManager
from app.services.job_seeder import generate_seed_jobs
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    job = JobModel(
        id=str(uuid.uuid4()),
        source=payload.source,
        external_id=payload.external_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        company_name=payload.company_name,
        apply_url=payload.apply_url,
        salary_range=payload.salary_range,
        job_type=payload.job_type,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    try:
        from app.metrics import JOB_CREATE_COUNT
        JOB_CREATE_COUNT.inc()
    except Exception:
        pass
    return job


@router.get("/", response_model=List[JobOut])
async def list_jobs(
    limit: int = 100,
    offset: int = 0,
    external_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        if external_id:
            q = await db.execute(
                select(JobModel)
                .where(JobModel.external_id == external_id)
                .limit(limit)
                .offset(offset)
            )
        else:
            q = await db.execute(
                select(JobModel)
                .order_by(JobModel.posted_at.desc().nullslast())
                .limit(limit)
                .offset(offset)
            )
        return q.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )


@router.get("/search", response_model=List[JobOut])
async def search_jobs(
    q: str = Query("", description="Search keyword"),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search jobs by keyword, location, or type."""
    stmt = select(JobModel)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                JobModel.title.ilike(pattern),
                JobModel.description.ilike(pattern),
                JobModel.company_name.ilike(pattern),
            )
        )
    if location:
        stmt = stmt.where(JobModel.location.ilike(f"%{location}%"))
    if job_type:
        stmt = stmt.where(JobModel.job_type.ilike(f"%{job_type}%"))
    stmt = stmt.order_by(JobModel.posted_at.desc().nullslast()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single job by ID."""
    job = await db.get(JobModel, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_jobs(db: AsyncSession = Depends(get_db)):
    """Seed the database with sample jobs from top-tier companies."""
    seed_data = generate_seed_jobs()
    count = 0
    for j in seed_data:
        job = JobModel(
            id=j["id"] if isinstance(j["id"], str) else str(j["id"]),
            source=j["source"],
            external_id=j["external_id"],
            title=j["title"],
            description=j["description"],
            location=j["location"],
            company_name=j["company_name"],
            apply_url=j["apply_url"],
            salary_range=j["salary_range"],
            job_type=j["job_type"],
            posted_at=datetime.fromisoformat(j["posted_at"]) if j.get("posted_at") else None,
        )
        db.add(job)
        count += 1
    await db.commit()
    return {"msg": f"Seeded {count} jobs successfully", "count": count}


@router.post("/{job_id}/embeddings", status_code=status.HTTP_201_CREATED)
async def create_job_embedding(job_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and save embedding for a job."""
    try:
        job = await db.get(JobModel, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        existing_embedding = await db.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.parent_type == "job",
                EmbeddingModel.parent_id == job_id,
            )
        )
        if existing_embedding.scalars().first():
            raise HTTPException(
                status_code=400, detail="Embedding already exists for this job"
            )
        embeddings_mgr = EmbeddingsManager()
        await embeddings_mgr.add_job_embedding(job_id, job.description, db)
        return {"msg": "Job embedding created successfully", "job_id": job_id, "status": "indexed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create job embedding: {str(e)}"
        )
