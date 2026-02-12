from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["init"])

@router.post("/init/schema", status_code=status.HTTP_201_CREATED, summary="Create Database Schema")
async def create_schema():
    """Create database and schema if they don't exist."""
    try:
        from app.db.session import engine
        from app.models.models import Base
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # First, try to create the database if it doesn't exist
        # Connect to the default postgres database
        db_url_parts = "postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x-pooler.ap-southeast-1.aws.neon.tech:5432/postgres"
        
        try:
            postgres_engine = create_async_engine(db_url_parts, echo=False, isolation_level="AUTOCOMMIT")
            async with postgres_engine.begin() as conn:
                # Check if neondb exists
                result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'neondb'"))
                db_exists = result.fetchone() is not None
                
                if not db_exists:
                    logger.info("Creating database 'neondb'...")
                    await conn.execute(text("CREATE DATABASE neondb"))
                    logger.info("Database 'neondb' created")
                else:
                    logger.info("Database 'neondb' already exists")
            
            await postgres_engine.dispose()
        except Exception as e:
            logger.warning(f"Could not create database (may already exist): {e}")
        
        # Now create the schema in the neondb
        logger.info("Creating database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Schema creation completed")
        return {"status": "ok", "message": "Schema created"}
    
    except Exception as e:
        logger.error(f"Schema creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Schema creation failed: {str(e)[:200]}"
        )
