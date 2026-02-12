from fastapi import APIRouter, HTTPException, status
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["init"])

@router.post("/init/schema", status_code=status.HTTP_201_CREATED, summary="Create Database Schema")
async def create_schema():
    """Create database schema if it doesn't exist."""
    try:
        from app.db.session import engine
        from app.models.models import Base
        
        logger.info("Creating database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        return {"status": "ok", "message": "Schema created"}
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema creation failed: {str(e)[:100]}"
        )
