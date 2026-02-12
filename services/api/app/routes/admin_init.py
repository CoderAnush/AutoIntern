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
        
        # Create schema in neondb using the configured connection
        logger.info("Creating schema tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Schema created successfully")
        return {"status": "ok", "message": "Schema initialized successfully"}
    
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)[:200]}")


@router.get("/init/health", summary="Database Health Check")
async def health():
    """Check if database is ready."""
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Database is ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)[:150]}")
