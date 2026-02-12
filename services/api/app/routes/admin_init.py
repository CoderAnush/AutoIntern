from fastapi import APIRouter, HTTPException, status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/init/create-schema", status_code=status.HTTP_201_CREATED)
async def create_database_schema():
    """Initialize database schema. Call this endpoint once after deployment."""
    try:
        logger.info("Creating database schema...")
        from app.db.session import engine
        from app.models.models import Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database schema created successfully")
        return {"status": "success", "message": "Database schema created"}
    
    except Exception as e:
        logger.error(f"Failed to create schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schema: {str(e)}"
        )

@router.get("/init/health")
async def init_health():
    """Check if database is ready."""
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT 1"))
        return {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
