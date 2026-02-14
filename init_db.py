import sys
sys.path.insert(0, "services/api")

import asyncio
import ssl
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

async def init_db():
    # Build connection string properly for asyncpg with SSL
    db_url = "postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x-pooler.ap-southeast-1.aws.neon.tech:5432/neondb?ssl=require"
    
    # Create async engine with SSL context
    engine = create_async_engine(
        db_url,
        echo=False,
        poolclass=NullPool,
        connect_args={
            "ssl": True,
            "server_settings": {"application_name": "AutoInternInit"}
        }
    )
    
    try:
        from app.models.models import Base
        
        async with engine.begin() as conn:
            print("Creating database schema...")
            await conn.run_sync(Base.metadata.create_all)
            print("Schema created successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
