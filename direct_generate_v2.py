import asyncio
import sys
import logging
import json

# Add services/api to path
sys.path.insert(0, "services/api")

from app.db.session import AsyncSessionLocal
from app.services.embeddings_service import EmbeddingsManager
from app.models.models import Job, Resume
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_embeddings_direct():
    print("🚀 Starting direct embeddings generation...")
    
    async with AsyncSessionLocal() as db:
        try:
            embeddings_mgr = EmbeddingsManager()
            
            # Process Jobs
            result = await db.execute(select(Job))
            jobs = result.scalars().all()
            print(f"📋 Found {len(jobs)} jobs")
            job_count = 0
            
            for job in jobs:
                try:
                    if job.description and len(job.description) > 20:
                        await embeddings_mgr.add_job_embedding(job.id, job.description, db)
                        job_count += 1
                        print(f"  ✅ Processed job {job.id}")
                except Exception as e:
                    print(f"  ❌ Failed job {job.id}: {e}")
                    
            # Process Resumes
            result = await db.execute(select(Resume))
            resumes = result.scalars().all()
            print(f"📄 Found {len(resumes)} resumes")
            resume_count = 0
            
            for resume in resumes:
                try:
                    if resume.parsed_text and len(resume.parsed_text) > 20:
                        await embeddings_mgr.add_resume_embedding(resume.id, resume.parsed_text, db)
                        resume_count += 1
                        print(f"  ✅ Processed resume {resume.id}")
                except Exception as e:
                    print(f"  ❌ Failed resume {resume.id}: {e}")
            
            print(f"\n✨ Generation Complete: {job_count} jobs, {resume_count} resumes")
            return True
            
        except Exception as e:
            print(f"❌ Critical Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(generate_embeddings_direct())
