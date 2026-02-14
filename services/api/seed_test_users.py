#!/usr/bin/env python3
"""
Test User Seeder Script
Populates the database with test users for development and E2E testing.
Run: python seed_test_users.py
"""

import sys
import asyncio
from uuid import uuid4

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.models.models import Base, User
from app.core.config import settings
from app.services.auth_service import AuthService


# Test credentials (use these for E2E testing)
TEST_USERS = [
    {
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User"
    },
    {
        "email": "demo@autointern.com",
        "password": "DemoPass123!",
        "name": "Demo User"
    },
    {
        "email": "admin@autointern.com",
        "password": "AdminPass123!",
        "name": "Admin User"
    },
    {
        "email": "john.doe@example.com",
        "password": "JohnDoe123!",
        "name": "John Doe"
    },
    {
        "email": "jane.smith@example.com",
        "password": "JaneSmith123!",
        "name": "Jane Smith"
    }
]


async def seed_users():
    """Seed test users into the database."""
    print("🌱 Starting test user seeding...\n")
    
    # Use SQLite with aiosqlite async driver for local development
    database_url = "sqlite+aiosqlite:///./autointern.db"
    
    # Create async engine with SQLite-specific configuration
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Don't create tables - they already exist from init_database.py
    print("📊 Using existing database schema...\n")
    
    # Create session factory
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            for user_data in TEST_USERS:
                email = user_data["email"].lower()
                
                # Check if user already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                existing_user = result.scalars().first()
                
                if existing_user:
                    print(f"⚠️  User already exists: {email}")
                    continue
                
                # Create new user with string UUID for SQLite compatibility
                password_hash = AuthService.hash_password(user_data["password"])
                new_user = User(
                    id=str(uuid4()),  # Convert UUID to string for SQLite
                    email=email,
                    password_hash=password_hash,
                    is_active=True,
                    notify_on_new_jobs=True,
                    notify_on_resume_upload=True,
                    notify_on_password_change=True,
                    weekly_digest=True,
                    email_frequency="weekly",
                    failed_login_attempts=0
                )
                
                session.add(new_user)
                print(f"✓ Created user: {email}")
            
            await session.commit()
            print("\n✅ Test users seeded successfully!\n")
            
            # Print credentials
            print("=" * 60)
            print("TEST CREDENTIALS FOR E2E TESTING")
            print("=" * 60)
            for user_data in TEST_USERS:
                print(f"\n📧 Email:    {user_data['email']}")
                print(f"🔑 Password: {user_data['password']}")
            print("\n" + "=" * 60)
            print("\n💡 Use these credentials to login and test the application.")
            print("📍 Frontend: http://localhost:3000/login")
            print("🔌 Backend:  http://localhost:8000/api\n")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding users: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(seed_users())
    sys.exit(0 if success else 1)
