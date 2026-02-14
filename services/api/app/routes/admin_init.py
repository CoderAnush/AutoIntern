from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["init"])

@router.get("/init/debug", summary="Debug Configuration")
async def debug_config():
    """Show debug info about configuration (safe to expose)."""
    from app.core.config import settings
    db_url = settings.database_url
    
    # Hide credentials
    safe_url = db_url.split('@')[0].replace(settings.database_url.split(':')[1], '***HIDDEN***') if '@' in db_url else db_url
    
    return {
        "database_url_safe": safe_url,
        "database_url_length": len(db_url),
        "has_trailing_newline": db_url.endswith('\n'),
        "stripped_url_length": len(db_url.strip()),
        "first_50_chars": db_url[:50].replace(settings.database_url.split('@')[0].split(':')[1], '***')
    }


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


@router.post("/init/migrate-jobs", status_code=200, summary="Add new Job columns")
async def migrate_jobs():
    """Add company_name, apply_url, salary_range, job_type to jobs table."""
    from app.db.session import engine
    results = []
    async with engine.begin() as conn:
        for col, dtype in [
            ("company_name", "VARCHAR(255)"),
            ("apply_url", "VARCHAR(1024)"),
            ("salary_range", "VARCHAR(255)"),
            ("job_type", "VARCHAR(64)"),
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} {dtype}"))
                results.append(f"Added {col}")
            except Exception as e:
                results.append(f"{col}: {str(e)[:80]}")
    return {"results": results}
