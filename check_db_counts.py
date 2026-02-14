import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'services', 'api'))
import asyncio
from app.db.session import SessionLocal
from app.models.models import Job
from sqlalchemy import select, func

async def check_jobs():
    async with SessionLocal() as db:
        result = await db.execute(select(func.count(Job.id)))
        count = result.scalar()
        print(f"Total Jobs in DB: {count}")

if __name__ == "__main__":
    asyncio.run(check_jobs())
