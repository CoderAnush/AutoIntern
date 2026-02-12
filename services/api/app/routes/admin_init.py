from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["init"])

@router.post("/init/schema", status_code=status.HTTP_201_CREATED, summary="Initialize Database Schema")
async def init_database():
    """Initialize database schema by creating all tables."""
    try:
        logger.info("Starting schema initialization...")
        
        from app.db.session import engine
        from app.models.models import Base
        
        # Create database - use direct Neon host (not pooler for admin operations)
        # First try to create database using direct connection
        direct_db_url = "postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x.us-east-1.aws.neon.tech/postgres?sslmode=require"
        
        from sqlalchemy.ext.asyncio import create_async_engine
        try:
            logger.info("Attempting to create base database...")
            admin_engine = create_async_engine(direct_db_url, echo=False,connect_args={"timeout": 10})
            
            async with admin_engine.begin() as conn:
                # Check if neondb exists
                result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname='neondb'"))
                if not result.fetchone():
                    logger.info("Creating neondb...")
                    await conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("CREATE DATABASE neondb"))
                    logger.info("neondb created")
            
            await admin_engine.dispose()
        except Exception as e:
            logger.warning(f"Database creation skipped: {e}")
        
        # Now create schema in neondb
        logger.info("Creating schema tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Schema created successfully")
        return {"status": "ok", "message": "Schema initialized"}
    
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)[:120]}")


@router.get("/init/health", summary="Database Health Check")
async def health():
    """Check if database is ready."""
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)[:100])
