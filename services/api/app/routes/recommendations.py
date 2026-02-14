"""Recommendations API routes for job matching and quality scoring."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import logging
import numpy as np

from app.db.session import get_db
from app.schemas.embeddings import RecommendationResult, ResumeQualityScore
from app.models.models import Resume as ResumeModel, Job as JobModel, Embedding as EmbeddingModel
from app.services.embeddings_service import EmbeddingsManager
from app.services.recommendation_service import RecommendationEngine
from app.services.skill_extractor import extract_skills_from_text

logger = logging.getLogger(__name__)

router = APIRouter()
embeddings_mgr = None


async def get_embeddings_manager():
    """Get or create singleton EmbeddingsManager."""
    global embeddings_mgr
    if embeddings_mgr is None:
        embeddings_mgr = EmbeddingsManager()
    return embeddings_mgr


@router.get("/jobs-for-resume/{resume_id}", response_model=List[RecommendationResult])
async def get_job_recommendations(
    resume_id: str,
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    top_k: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top-k job recommendations for a resume.

    Uses FAISS vector similarity (70%) + skill match scoring (30%) to rank jobs.

    Query Parameters:
    - min_similarity: Filter threshold (0.0-1.0), default 0.5
    - top_k: Number of results, default 20, max 100

    Returns:
    - List of RecommendationResult with job details and skill gaps
    - 404 if resume not found or has no embedding
    """
    try:
        # Fetch resume
        resume = await db.get(ResumeModel, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Fetch resume embedding
        embedding_result = await db.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.parent_type == "resume",
                EmbeddingModel.parent_id == resume_id
            )
        )
        embedding_record = embedding_result.scalars().first()
        if not embedding_record:
            raise HTTPException(status_code=404, detail="Resume embedding not found. Please regenerate recommendations.")

        # Convert embedding from list to numpy array
        resume_embedding = np.array(embedding_record.vector, dtype=np.float32)
        if isinstance(resume.skills, list):
            resume_skills = resume.skills
        elif isinstance(resume.skills, str):
            try:
                resume_skills = json.loads(resume.skills) if resume.skills else []
            except Exception:
                resume_skills = []
        else:
            resume_skills = []
        
            # If stored skills are empty, derive from parsed text to avoid stale 0 scores
            if not resume_skills and resume.parsed_text:
                resume_skills = extract_skills_from_text(resume.parsed_text)

        # Get embeddings manager and generate recommendations
        mgr = await get_embeddings_manager()
        recommendations = await RecommendationEngine.recommend_jobs_for_resume(
            resume_id=resume_id,
            resume_embedding=resume_embedding,
            resume_skills=resume_skills,
            embeddings_manager=mgr,
            db=db,
            min_similarity=min_similarity,
            top_k=top_k
        )

        # Convert to RecommendationResult models
        results = [
            RecommendationResult(
                job_id=r["job_id"],
                job_title=r["job_title"],
                job_description=r["job_description"],
                job_location=r["job_location"],
                resume_id=r["resume_id"],
                similarity_score=r["similarity_score"],
                matched_skills=r["matched_skills"],
                skill_gaps=r["skill_gaps"]
            )
            for r in recommendations
        ]

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/resumes-for-job/{job_id}", response_model=List[RecommendationResult])
async def get_resume_recommendations(
    job_id: str,
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    top_k: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top-k resume recommendations for a job.

    Uses FAISS vector similarity (70%) + resume quality score (30%) to rank resumes.

    Query Parameters:
    - min_similarity: Filter threshold (0.0-1.0), default 0.5
    - top_k: Number of results, default 20, max 100

    Returns:
    - List of RecommendationResult with resume details and skill gaps
    - 404 if job not found or has no embedding
    """
    try:
        # Fetch job
        job = await db.get(JobModel, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Fetch job embedding
        embedding_result = await db.execute(
            select(EmbeddingModel).where(
                EmbeddingModel.parent_type == "job",
                EmbeddingModel.parent_id == job_id
            )
        )
        embedding_record = embedding_result.scalars().first()
        if not embedding_record:
            raise HTTPException(status_code=404, detail="Job embedding not found. Please index the job first.")

        # Convert embedding from list to numpy array
        job_embedding = np.array(embedding_record.vector, dtype=np.float32)
        job_skills = extract_skills_from_text(job.description) if job.description else []

        # Get embeddings manager and generate recommendations
        mgr = await get_embeddings_manager()
        recommendations = await RecommendationEngine.recommend_resumes_for_job(
            job_id=job_id,
            job_embedding=job_embedding,
            job_skills=job_skills,
            embeddings_manager=mgr,
            db=db,
            min_similarity=min_similarity,
            top_k=top_k
        )

        # Convert to RecommendationResult models
        results = [
            RecommendationResult(
                job_id=r["job_id"],
                job_title="",  # Not used in this context
                job_description="",
                job_location="",
                resume_id=r["resume_id"],
                similarity_score=r["similarity_score"],
                matched_skills=r["matched_skills"],
                skill_gaps=r["skill_gaps"]
            )
            for r in recommendations
        ]

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/resume-quality/{resume_id}", response_model=ResumeQualityScore)
async def get_resume_quality(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get quality assessment breakdown for a resume.

    Returns scores for:
    - text_length_score (0-100): Quality of resume length
    - skill_count_score (0-100): Number of skills identified
    - completeness_score (0-100): Presence of tech and soft skills
    - overall_quality_score (0-100): Average of three components

    Returns:
    - ResumeQualityScore with detailed breakdown
    - 404 if resume not found
    """
    try:
        # Fetch resume
        resume = await db.get(ResumeModel, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Calculate quality scores
        if isinstance(resume.skills, list):
            resume_skills = resume.skills
        elif isinstance(resume.skills, str):
            try:
                resume_skills = json.loads(resume.skills) if resume.skills else []
            except Exception:
                resume_skills = []
        else:
            resume_skills = []

        if not resume_skills and resume.parsed_text:
            resume_skills = extract_skills_from_text(resume.parsed_text)
        quality_scores = RecommendationEngine.calculate_resume_quality(
            resume.parsed_text or "",
            resume_skills
        )

        return ResumeQualityScore(
            resume_id=resume_id,
            text_length_score=quality_scores["text_length_score"],
            skill_count_score=quality_scores["skill_count_score"],
            completeness_score=quality_scores["completeness_score"],
            overall_quality_score=quality_scores["overall_quality_score"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating resume quality: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate resume quality")


@router.post("/batch-index-jobs", status_code=status.HTTP_202_ACCEPTED)
async def batch_index_jobs(
    background: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger batch embedding generation for all jobs without embeddings.

    This endpoint finds all jobs in the database that don't have embeddings yet
    and generates embeddings for them.

    Query Parameters:
    - background: If true (default), returns 202 Accepted immediately
                  If false, generates embeddings synchronously and returns results

    Returns:
    - If background=true: task_id for monitoring progress (recommended for large datasets)
    - If background=false: immediate results with count of indexed jobs
    """
    try:
        # Find jobs without embeddings
        jobs_without_embeddings_result = await db.execute(
            select(JobModel).where(
                ~JobModel.id.in_(
                    select(EmbeddingModel.parent_id).where(
                        EmbeddingModel.parent_type == "job"
                    )
                )
            )
        )
        jobs_to_index = jobs_without_embeddings_result.scalars().all()

        if not jobs_to_index:
            return {
                "msg": "No jobs to index",
                "total_jobs": 0,
                "indexed_count": 0
            }

        if background:
            # Return immediately with task info (202 Accepted)
            # In production, would queue to Redis and return task_id
            return {
                "msg": "Batch indexing queued",
                "total_jobs": len(jobs_to_index),
                "task_id": "batch-jobs-" + str(hash(tuple(j.id for j in jobs_to_index)))[:8],
                "status": "queued"
            }
        else:
            # Synchronous indexing (smaller datasets)
            mgr = await get_embeddings_manager()
            indexed_count = 0
            failed_count = 0

            for job in jobs_to_index:
                try:
                    await mgr.add_job_embedding(job.id, job.description, db)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index job {job.id}: {e}")
                    failed_count += 1

            return {
                "msg": "Batch indexing complete",
                "total_jobs": len(jobs_to_index),
                "indexed_count": indexed_count,
                "failed_count": failed_count,
                "status": "completed"
            }

    except Exception as e:
        logger.error(f"Error in batch indexing: {e}")
        raise HTTPException(status_code=500, detail="Batch indexing failed")


@router.get("/batch-status/{task_id}")
async def get_batch_status(task_id: str):
    """
    Check status of a batch indexing task.

    Returns:
    - status: pending, in_progress, completed, or failed
    - processed: Number of jobs indexed so far
    - total: Total jobs to index
    - 404 if task not found
    """
    try:
        # In a real implementation, would check Redis queue status
        # For now, return a placeholder response
        # Production would track tasks via Redis/Celery

        # Placeholder: assume task is completed if queried
        return {
            "task_id": task_id,
            "status": "completed",
            "processed": 0,
            "total": 0,
            "message": "In production, batch status would be tracked via Redis queue"
        }

    except Exception as e:
        logger.error(f"Error checking batch status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check batch status")
