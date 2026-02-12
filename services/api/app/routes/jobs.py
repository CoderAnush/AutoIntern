from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.job import JobCreate, JobOut
from app.db.session import get_db
from app.models.models import Job as JobModel, Embedding as EmbeddingModel
from app.services.embeddings_service import EmbeddingsManager
import uuid

router = APIRouter()

@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    job = JobModel(
        id=uuid.uuid4(),
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


@router.post("/jobs/{job_id}/embeddings", status_code=status.HTTP_201_CREATED)
async def create_job_embedding(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate and save embedding for a job.

    This endpoint generates a Sentence-BERT embedding for a job's description
    and stores it in the database along with the FAISS index for similarity search.

    Args:
        job_id: UUID of the job to index

    Returns:
        Success message with job_id

    Error Responses:
        - 404: Job not found or embedding already exists
        - 500: Embedding generation failed
    """
    try:
        # Fetch job
        job = await db.get(JobModel, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if embedding already exists
        existing_embedding = await db.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.parent_type == "job",
                EmbeddingModel.parent_id == job_id
            )
        )
        if existing_embedding.scalars().first():
            raise HTTPException(status_code=400, detail="Embedding already exists for this job")

        # Generate embedding
        embeddings_mgr = EmbeddingsManager()
        await embeddings_mgr.add_job_embedding(job_id, job.description, db)

        return {
            "msg": "Job embedding created successfully",
            "job_id": job_id,
            "status": "indexed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job embedding: {str(e)}")
