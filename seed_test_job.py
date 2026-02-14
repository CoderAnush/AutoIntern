import sys
import os
import asyncio
from datetime import datetime

# Add services/api to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api'))

from app.db.session import AsyncSessionLocal
from app.models.models import Job

async def seed_job():
    async with AsyncSessionLocal() as db:
        job = Job(
            title="Python Developer",
            company_name="Tech Corp",
            location="Remote",
            description="We are looking for a Python Developer with clean code skills. Experience with FastAPI and React is a plus.",
            posted_at=datetime.utcnow(),
            source="manual_seed",
            apply_url="https://example.com/apply"
        )
        db.add(job)
        await db.commit()
        print(f"✅ Seeded Job: {job.id}")

if __name__ == "__main__":
    asyncio.run(seed_job())
