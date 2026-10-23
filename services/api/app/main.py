# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoIntern API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes with error handling
from app.routes import health

# Always include health router
app.include_router(health.router)

# Include initialization router
try:
    from app.routes import admin_init
    app.include_router(admin_init.router)
    logger.info("✓ Initialization endpoints loaded")
except Exception as e:
    logger.warning(f"✗ Initialization endpoints failed: {e}")

# Try to include feature routers (they may fail if external services are unavailable)
try:
    from app.routes import users
    app.include_router(users.router, prefix="/api/auth", tags=["auth"])
    logger.info("✓ Users/Auth router loaded")
except Exception as e:
    logger.warning(f"✗ Users/Auth router failed: {e}")

try:
    from app.routes import jobs
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    logger.info("✓ Jobs router loaded")
except Exception as e:
    logger.warning(f"✗ Jobs router failed: {e}")

try:
    from app.routes import resumes
    app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
    logger.info("✓ Resumes router loaded")
except Exception as e:
    logger.warning(f"✗ Resumes router failed: {e}")

try:
    from app.routes import applications
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
    logger.info("✓ Applications router loaded")
except Exception as e:
    logger.warning(f"✗ Applications router failed: {e}")

try:
    from app.routes import recommendations
    app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
    logger.info("✓ Recommendations router loaded")
except Exception as e:
    logger.warning(f"✗ Recommendations router failed: {e}")

try:
    from app.routes import admin
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    logger.info("✓ Admin router loaded")
except Exception as e:
    logger.warning(f"✗ Admin router failed: {e}")

try:
    from app.routes import emails
    app.include_router(emails.router, prefix="/api", tags=["emails"])
    logger.info("✓ Emails router loaded")
except Exception as e:
    logger.warning(f"✗ Emails router failed: {e}")

try:
    from app.routes import preferences
    app.include_router(preferences.router, prefix="/api", tags=["preferences"])
    logger.info("✓ Preferences router loaded")
except Exception as e:
    logger.warning(f"✗ Preferences router failed: {e}")

try:
    from app.routes import saved_jobs
    app.include_router(saved_jobs.router, prefix="/api", tags=["saved-jobs"])
    logger.info("✓ Saved-jobs router loaded")
except Exception as e:
    logger.warning(f"✗ Saved-jobs router failed: {e}")

try:
    from app.routes import ai_features
    app.include_router(ai_features.router, prefix="/api", tags=["ai"])
    logger.info("✓ AI features router loaded")
except Exception as e:
    logger.warning(f"✗ AI features router failed: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup (non-blocking)."""
    logger.info("✓ Application started successfully - health check available")

    # Auto-run migrations if configured (useful for dev/SQLite)
    if settings.migrate_on_start:
        try:
            from alembic.config import Config
            from alembic import command
            import os
            alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
            alembic_cfg = Config(alembic_ini)
            command.upgrade(alembic_cfg, "head")
            logger.info("✓ Database migrations applied")
        except Exception as e:
            logger.warning(f"Auto-migration failed (non-critical): {e}")

    # For SQLite dev: create all tables directly if they don't exist
    try:
        from app.models.base import Base
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database tables verified/created")
    except Exception as e:
        logger.warning(f"Table creation check failed: {e}")

    # Add is_india_job column to existing jobs tables that predate this migration
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            if settings.database_url.startswith("sqlite"):
                # SQLite: check via PRAGMA, add if missing
                result = await conn.execute(text("PRAGMA table_info(jobs)"))
                cols = {row[1] for row in result.fetchall()}
                if "is_india_job" not in cols:
                    await conn.execute(text(
                        "ALTER TABLE jobs ADD COLUMN is_india_job BOOLEAN DEFAULT 0"
                    ))
                    logger.info("✓ Added is_india_job column to jobs table")
            else:
                # PostgreSQL: add column if not exists
                await conn.execute(text(
                    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_india_job BOOLEAN DEFAULT FALSE"
                ))
    except Exception as e:
        logger.warning(f"is_india_job column migration (non-critical): {e}")

    # Back-fill is_india_job for existing jobs from known Indian companies
    try:
        from app.db.session import engine
        from app.services.india_companies import get_indian_origin_names
        from sqlalchemy import text
        indian_names = list(get_indian_origin_names())
        # Escape single quotes for SQL safety (SQLite uses '' to escape ')
        def _sql_str(s: str) -> str:
            return "'" + s.replace("'", "''") + "'"
        placeholders = ",".join(_sql_str(n) for n in indian_names)
        async with engine.begin() as conn:
            result = await conn.execute(text(
                f"UPDATE jobs SET is_india_job=1 "
                f"WHERE (is_india_job IS NULL OR is_india_job=0) "
                f"AND LOWER(company_name) IN ({placeholders})"
            ))
            updated = result.rowcount if hasattr(result, "rowcount") else "?"
            if updated:
                logger.info(f"✓ Back-filled is_india_job=1 for {updated} historical Indian company jobs")
    except Exception as e:
        logger.warning(f"is_india_job back-fill (non-critical): {e}")


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """HTTP middleware for request processing."""
    response = await call_next(request)
    return response


@app.get("/metrics")
async def metrics():
    """Get current metrics (stub)."""
    return {"error": "metrics unavailable"}


@app.get("/metrics/summary")
async def metrics_summary():
    """Get performance metrics summary (stub)."""
    return {"metrics": "placeholder"}


@app.get("/test-reload")
async def test_reload():
    """Test if server reloaded."""
    return {"message": "Server reloaded successfully", "admin_loaded": "yes"}


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Return running status and next fire times for all schedulers."""
    from apscheduler.schedulers.base import STATE_RUNNING
    status = {}
    try:
        if _email_scheduler and _email_scheduler.scheduler.state == STATE_RUNNING:
            job = _email_scheduler.scheduler.get_job("daily_email_digest")
            status["email_scheduler"] = {
                "running": True,
                "next_run": str(job.next_run_time) if job else None,
                "timezone": "Asia/Kolkata",
                "schedule": "07:00 IST daily",
            }
        else:
            status["email_scheduler"] = {"running": False}
    except Exception as e:
        status["email_scheduler"] = {"running": False, "error": str(e)}
    try:
        if _job_scheduler and _job_scheduler.scheduler.state == STATE_RUNNING:
            job = _job_scheduler.scheduler.get_job("daily_job_scrape")
            status["job_scheduler"] = {
                "running": True,
                "next_run": str(job.next_run_time) if job else None,
                "schedule": "hourly at :00",
            }
        else:
            status["job_scheduler"] = {"running": False}
    except Exception as e:
        status["job_scheduler"] = {"running": False, "error": str(e)}
    return status


@app.post("/api/scheduler/trigger")
async def trigger_scrape_now():
    """Manually trigger an immediate job scrape (no auth — use admin token in prod)."""
    try:
        if _job_scheduler:
            import threading
            t = threading.Thread(target=_job_scheduler.run_daily_scrape, daemon=True)
            t.start()
            return {"msg": "Scrape triggered", "status": "started"}
        return {"msg": "Job scheduler not running", "status": "unavailable"}
    except Exception as e:
        return {"msg": f"Error: {e}", "status": "error"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    pass


# Initialize and start daily email scheduler
try:
    from app.services.daily_email_scheduler import DailyEmailScheduler
    _email_scheduler = DailyEmailScheduler()
    _email_scheduler.start()
    logger.info("✓ Daily email scheduler initialized - digest at 07:00 IST (Asia/Kolkata)")
except Exception as e:
    logger.warning(f"⚠️ Email scheduler could not start: {e}")

# Initialize and start daily job scraper scheduler
_job_scheduler = None
try:
    from app.services.daily_job_scheduler import DailyJobScheduler
    from app.routes.admin import set_job_scheduler
    _job_scheduler = DailyJobScheduler(hour=None, minute=0)  # Run hourly at :00
    set_job_scheduler(_job_scheduler)
    _job_scheduler.start()
    logger.info("✓ Daily job scheduler initialized - scraping fresh jobs every hour at :00")

    # Trigger immediate scrape on startup if jobs table is empty
    import asyncio
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Job as JobModel

    async def _immediate_scrape_if_empty():
        """Check if jobs table is empty and trigger immediate scrape."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(JobModel.id))
                job_count = len(result.scalars().all())

                if job_count == 0:
                    logger.info("📌 Jobs table is empty - triggering immediate scrape on startup...")
                    _job_scheduler.run_daily_scrape()
                else:
                    logger.info(f"✓ Database has {job_count} jobs already")
        except Exception as e:
            logger.warning(f"Could not check job count on startup: {e}")

    # Schedule the check as a background task
    try:
        asyncio.create_task(_immediate_scrape_if_empty())
    except Exception as e:
        logger.warning(f"Could not schedule immediate scrape check: {e}")

except Exception as e:
    logger.warning(f"⚠️ Job scheduler could not start: {e}")
