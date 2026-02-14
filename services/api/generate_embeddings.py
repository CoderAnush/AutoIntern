#!/usr/bin/env python3
"""
Generate Embeddings for Jobs and Resumes
This script generates AI embeddings for all jobs and resumes in the database
to enable job recommendations and resume quality analysis.
"""

import sys
import asyncio
import logging

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.models import Job as JobModel, Resume as ResumeModel, Embedding as EmbeddingModel
from app.services.embeddings_service import EmbeddingsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_embeddings():
    """Generate embeddings for all jobs and resumes."""
    print("\n" + "="*60)
    print("  🤖 AI Embeddings Generation")
    print("="*60 + "\n")
    
    # Use SQLite with aiosqlite async driver
    database_url = "sqlite+aiosqlite:///./autointern.db"
    
    # Create async engine with proper configuration
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True  # Enable SQLAlchemy 2.0 style
    )
    
    # Create session factory
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )
    
    try:
        # Initialize embeddings manager (loads Sentence-BERT model)
        print("📥 Loading Sentence-BERT model...")
        embeddings_mgr = EmbeddingsManager()
        print("✅ Model loaded successfully!\n")
        
        async with async_session() as session:
            # Generate job embeddings
            print("="*60)
            print("  📋 Processing Jobs")
            print("="*60 + "\n")
            
            # Find jobs without embeddings
            jobs_result = await session.execute(
                select(JobModel).where(
                    ~JobModel.id.in_(
                        select(EmbeddingModel.parent_id).where(
                            EmbeddingModel.parent_type == "job"
                        )
                    )
                )
            )
            jobs_to_process = jobs_result.scalars().all()
            
            print(f"Found {len(jobs_to_process)} jobs without embeddings\n")
            
            job_success = 0
            job_failed = 0
            
            for i, job in enumerate(jobs_to_process, 1):
                try:
                    if not job.description or len(job.description.strip()) < 20:
                        print(f"  ⚠️  Job {i}/{len(jobs_to_process)}: Skipped (description too short)")
                        job_failed += 1
                        continue
                    
                    await embeddings_mgr.add_job_embedding(
                        job_id=job.id,
                        job_text=job.description,
                        db=session
                    )
                    print(f"  ✓ Job {i}/{len(jobs_to_process)}: {job.title[:50]}")
                    job_success += 1
                    
                except Exception as e:
                    print(f"  ✗ Job {i}/{len(jobs_to_process)}: Failed - {str(e)[:50]}")
                    job_failed += 1
            
            print(f"\n📊 Jobs: {job_success} successful, {job_failed} failed\n")
            
            # Generate resume embeddings
            print("="*60)
            print("  📄 Processing Resumes")
            print("="*60 + "\n")
            
            # Find resumes without embeddings
            resumes_result = await session.execute(
                select(ResumeModel).where(
                    ~ResumeModel.id.in_(
                        select(EmbeddingModel.parent_id).where(
                            EmbeddingModel.parent_type == "resume"
                        )
                    )
                )
            )
            resumes_to_process = resumes_result.scalars().all()
            
            print(f"Found {len(resumes_to_process)} resumes without embeddings\n")
            
            resume_success = 0
            resume_failed = 0
            
            for i, resume in enumerate(resumes_to_process, 1):
                try:
                    if not resume.parsed_text or len(resume.parsed_text.strip()) < 20:
                        print(f"  ⚠️  Resume {i}/{len(resumes_to_process)}: Skipped (text too short)")
                        resume_failed += 1
                        continue
                    
                    await embeddings_mgr.add_resume_embedding(
                        resume_id=resume.id,
                        resume_text=resume.parsed_text,
                        db=session
                    )
                    print(f"  ✓ Resume {i}/{len(resumes_to_process)}: {resume.file_name or 'Unnamed'}")
                    resume_success += 1
                    
                except Exception as e:
                    print(f"  ✗ Resume {i}/{len(resumes_to_process)}: Failed - {str(e)[:50]}")
                    resume_failed += 1
            
            print(f"\n📊 Resumes: {resume_success} successful, {resume_failed} failed\n")
            
            # Summary
            print("="*60)
            print("  ✅ Embeddings Generation Complete!")
            print("="*60 + "\n")
            
            total_success = job_success + resume_success
            total_failed = job_failed + resume_failed
            
            print(f"Total Embeddings Generated: {total_success}")
            print(f"Total Failed: {total_failed}")
            print(f"\n💡 AI recommendations are now enabled!")
            print(f"🔗 Test at: http://localhost:8000/api/recommendations/\n")
            
            return total_success > 0
            
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\n📦 Install required packages:")
        print("   pip install sentence-transformers faiss-cpu\n")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(generate_embeddings())
    sys.exit(0 if success else 1)
