"""
Initialize SQLite database with all required tables and seed data
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.models import User, Job, Resume, Application, Company, Embedding, EmailLog, RequestLog
from app.core.config import settings
import uuid
from datetime import datetime, timedelta

async def init_database():
    """Create all tables in SQLite database."""
    print("🔧 Initializing SQLite database...")
    print(f"📁 Database URL: {settings.database_url}")
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        print("\n📋 Creating tables...")
        await conn.run_sync(Base.metadata.drop_all)  # Drop existing tables
        await conn.run_sync(Base.metadata.create_all)  # Create fresh tables
        print("✅ All tables created successfully!")
    
    # Create session maker
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Seed data
    async with async_session() as session:
        print("\n🌱 Seeding database with sample data...")
        
        # Seed jobs
        jobs = [
            Job(
                id=str(uuid.uuid4()),
                source="internal",
                external_id=f"job-{i}",
                title=title,
                description=f"Exciting opportunity as {title} at {company}. Work on cutting-edge projects!",
                location=location,
                company_name=company,
                apply_url=f"https://careers.{company.lower().replace(' ', '')}.com/jobs/{i}",
                salary_range=salary,
                job_type=job_type,
                posted_at=datetime.now() - timedelta(days=i)
            )
            for i, (title, company, location, salary, job_type) in enumerate([
                ("Software Engineer", "Google", "Mountain View, CA", "$120k-$180k", "Full-time"),
                ("Frontend Developer", "Microsoft", "Seattle, WA", "$110k-$160k", "Full-time"),
                ("Backend Engineer", "Amazon", "New York, NY", "$130k-$190k", "Full-time"),
                ("Data Scientist", "Meta", "Menlo Park, CA", "$140k-$200k", "Full-time"),
                ("DevOps Engineer", "Netflix", "Los Gatos, CA", "$125k-$175k", "Full-time"),
                ("Full Stack Developer", "Apple", "Cupertino, CA", "$135k-$185k", "Full-time"),
                ("Machine Learning Engineer", "Tesla", "Palo Alto, CA", "$150k-$210k", "Full-time"),
                ("Cloud Architect", "Salesforce", "San Francisco, CA", "$160k-$220k", "Full-time"),
                ("Product Manager", "LinkedIn", "Sunnyvale, CA", "$140k-$190k", "Full-time"),
                ("UX Designer", "Adobe", "San Jose, CA", "$100k-$150k", "Full-time"),
            ])
        ]
        
        for job in jobs:
            session.add(job)
        
        print(f"✅ Added {len(jobs)} jobs")
        
        await session.commit()
        print("\n🎉 Database initialization complete!")
        
    await engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AutoIntern Database Initialization")
    print("=" * 60)
    asyncio.run(init_database())
    print("\n✅ Database is ready to use!")
