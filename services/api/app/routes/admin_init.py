from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncEngine
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["init"])

@router.post("/init/schema", status_code=status.HTTP_201_CREATED, summary="Initialize Database")
async def init_database():
    """Initialize database and create schema."""
    try:
        logger.info("Starting database initialization...")
        
        # Import configuration
        from app.core.config import settings
        from app.db.session import engine
        from app.models.models import Base
        
        # First, check if we can create the database by connecting to the default postgres db
        # Use a workaround for pooler: connect directly to the server, not through pooler
        database_url = "postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x.neon.tech:5432/postgres?sslmode=require"
        
        from sqlalchemy.ext.asyncio import create_async_engine
        
        try:
            logger.info("Attempting to create neondb database...")
            admin_engine = create_async_engine(database_url, echo=False)
            
            async with admin_engine.begin() as conn:
                # Create database if it doesn't exist
                result = await conn.execute(text("SELECT datname FROM pg_database WHERE datname = 'neondb'"))
                if not result.fetchone():
                    logger.info("Creating database neondb...")
                    await conn.execute(text("CREATE DATABASE neondb"))
                    logger.info("Database created successfully")
                else:
                    logger.info("Database neondb already exists")
            
            await admin_engine.dispose()
        except Exception as db_err:
            logger.warning(f"Could not create database (may already exist or pooler limitation): {db_err}")
            # Continue anyway - the database might already exist
        
        # Now create all tables in the neondb
        logger.info("Creating schema in neondb...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Schema created successfully")
        return {
            "status": "ok",
            "message": "Database and schema initialized successfully"
        }
    
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Initialization failed: {str(e)[:150]}"
        )


@router.get("/init/health", summary="Check Initialization Status")
async def check_health():
    """Check if database is accessible and ready."""
    try:
        from app.db.session import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.fetchone():
                return {"status": "ok", "message": "Database is accessible"}
        
        raise Exception("Database query returned no result")
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database not ready: {str(e)}"
        )
