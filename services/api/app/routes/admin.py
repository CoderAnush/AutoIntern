from app.db.session import AsyncSessionLocal

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
