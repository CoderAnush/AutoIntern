#!/usr/bin/env python3
"""
Generate Embeddings for Jobs and Resumes (Synchronous Version)
This script generates AI embeddings for all jobs and resumes in the database
using synchronous SQLAlchemy to avoid async issues.
"""

import sys
import logging
import numpy as np

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, ".")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from uuid import uuid4

from app.models.models import Job as JobModel, Resume as ResumeModel, Embedding as EmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embeddings():
    """Generate embeddings for all jobs and resumes."""
    print("\n" + "="*60)
    print("  🤖 AI Embeddings Generation (Sync)")
    print("="*60 + "\n")
    
    # Use SQLite with synchronous driver
    database_url = "sqlite:///./autointern.db"
    
    # Create synchronous engine
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    
    try:
        # Initialize embeddings manager (loads Sentence-BERT model)
        print("📥 Loading Sentence-BERT model...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Model loaded successfully!\n")
        
        # Initialize FAISS index
        print("📊 Initializing FAISS index...")
        import faiss
        embedding_dim = 384
        faiss_index = faiss.IndexFlatL2(embedding_dim)
        print("✅ FAISS index initialized!\n")
        
        session = SessionLocal()
        
        try:
            # Generate job embeddings
            print("="*60)
            print("  📋 Processing Jobs")
            print("="*60 + "\n")
            
            # Find jobs without embeddings
            jobs_with_embeddings = session.query(EmbeddingModel.parent_id).filter(
                EmbeddingModel.parent_type == "job"
            ).all()
            job_ids_with_embeddings = {e[0] for e in jobs_with_embeddings}
            
            jobs = session.query(JobModel).all()
            jobs_to_process = [j for j in jobs if j.id not in job_ids_with_embeddings]
            
            print(f"Found {len(jobs_to_process)} jobs without embeddings\n")
            
            job_success = 0
            job_failed = 0
            
            for i, job in enumerate(jobs_to_process, 1):
                try:
                    if not job.description or len(job.description.strip()) < 20:
                        print(f"  ⚠️  Job {i}/{len(jobs_to_process)}: Skipped (description too short)")
                        job_failed += 1
                        continue
                    
                    # Generate embedding
                    embedding_vector = model.encode(job.description.strip(), convert_to_numpy=True)
                    embedding_vector = embedding_vector.astype(np.float32)
                    
                    # Add to FAISS index
                    faiss_index.add(np.array([embedding_vector]))
                    
                    # Save to database
                    embedding_record = EmbeddingModel(
                        id=str(uuid4()),
                        parent_type="job",
                        parent_id=job.id,
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        vector=embedding_vector.tolist()
                    )
                    session.add(embedding_record)
                    session.commit()
                    
                    print(f"  ✓ Job {i}/{len(jobs_to_process)}: {job.title[:50]}")
                    job_success += 1
                    
                except Exception as e:
                    session.rollback()
                    print(f"  ✗ Job {i}/{len(jobs_to_process)}: Failed - {str(e)[:50]}")
                    job_failed += 1
            
            print(f"\n📊 Jobs: {job_success} successful, {job_failed} failed\n")
            
            # Generate resume embeddings
            print("="*60)
            print("  📄 Processing Resumes")
            print("="*60 + "\n")
            
            # Find resumes without embeddings
            resumes_with_embeddings = session.query(EmbeddingModel.parent_id).filter(
                EmbeddingModel.parent_type == "resume"
            ).all()
            resume_ids_with_embeddings = {e[0] for e in resumes_with_embeddings}
            
            resumes = session.query(ResumeModel).all()
            resumes_to_process = [r for r in resumes if r.id not in resume_ids_with_embeddings]
            
            print(f"Found {len(resumes_to_process)} resumes without embeddings\n")
            
            resume_success = 0
            resume_failed = 0
            
            for i, resume in enumerate(resumes_to_process, 1):
                try:
                    if not resume.parsed_text or len(resume.parsed_text.strip()) < 20:
                        print(f"  ⚠️  Resume {i}/{len(resumes_to_process)}: Skipped (text too short)")
                        resume_failed += 1
                        continue
                    
                    # Generate embedding
                    embedding_vector = model.encode(resume.parsed_text.strip(), convert_to_numpy=True)
                    embedding_vector = embedding_vector.astype(np.float32)
                    
                    # Add to FAISS index
                    faiss_index.add(np.array([embedding_vector]))
                    
                    # Save to database
                    embedding_record = EmbeddingModel(
                        id=str(uuid4()),
                        parent_type="resume",
                        parent_id=resume.id,
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        vector=embedding_vector.tolist()
                    )
                    session.add(embedding_record)
                    session.commit()
                    
                    print(f"  ✓ Resume {i}/{len(resumes_to_process)}: {resume.file_name or 'Unnamed'}")
                    resume_success += 1
                    
                except Exception as e:
                    session.rollback()
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
            
        finally:
            session.close()
            
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
        engine.dispose()


if __name__ == "__main__":
    success = generate_embeddings()
    sys.exit(0 if success else 1)
