import asyncio
import sys
import logging
import json
from uuid import uuid4

# Add services/api to path
sys.path.insert(0, "services/api")

from app.db.session import AsyncSessionLocal
from app.services.embeddings_service import EmbeddingsManager
from app.models.models import Resume, User
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_resume_entry():
    print("🚀 Creating Resume + Embedding...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get test user
            result = await db.execute(select(User).where(User.email == "test@example.com"))
            user = result.scalars().first()
            
            if not user:
                print("❌ User test@example.com not found")
                return False
                
            print(f"👤 Found user: {user.email} ({user.id})")
            
            # Create Resume
            resume_text = """
            Software Engineer with 5 years of experience in Python, FastAPI, and React.
            Skilled in cloud computing (AWS), Docker, and Kubernetes.
            Previous experience at TechCorp building scalable microservices.
            Education: BS in Computer Science from University of Tech.
            """
            
            resume_id = str(uuid4())
            resume = Resume(
                id=resume_id,
                user_id=user.id,
                file_name="test_resume.pdf",
                parsed_text=resume_text,
                skills=json.dumps(["Python", "FastAPI", "React", "AWS", "Docker"]),
                storage_url="uploads/resumes/test_resume.pdf"
            )
            
            db.add(resume)
            await db.commit()
            print(f"📄 Created resume: {resume_id}")
            
            # Generate Embedding
            embeddings_mgr = EmbeddingsManager()
            await embeddings_mgr.add_resume_embedding(resume_id, resume_text, db)
            print("✨ Generated embedding for resume")
            
            # Test Recommendations
            print("\n🔍 Testing Recommendations...")
            # embedding_record = await embeddings_mgr.get_embedding("resume", resume_id, db) 
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(create_resume_entry())
