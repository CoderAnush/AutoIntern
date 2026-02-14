import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_migrations():
    # Set the database URL
    db_url = "postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    # Create async engine
    engine = create_async_engine(db_url, echo=False)
    
    try:
        # Import Base models
        import sys
        sys.path.insert(0, "c:/Users/anush/Desktop/AutoIntern/AutoIntern/services/api")
        from app.models.models import Base
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✓ Database schema created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating schema: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migrations())
