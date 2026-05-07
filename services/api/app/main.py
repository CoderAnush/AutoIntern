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


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup (non-blocking)."""
    logger.info("✓ Application started successfully - health check available")

    import asyncio

    async def background_initialization():
        """Run all expensive operations in background."""
        try:
            logger.info("Starting background initialization tasks...")
            logger.info("Background tasks complete")

        except Exception as e:
            logger.warning(f"Background initialization error (non-critical): {e}")

    # Schedule as background task - don't wait
    try:
        asyncio.create_task(background_initialization())
    except Exception as e:
        logger.warning(f"Could not schedule background task: {e}")


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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    pass


# Initialize and start daily email scheduler
try:
    from app.services.daily_email_scheduler import DailyEmailScheduler
    _email_scheduler = DailyEmailScheduler()
    _email_scheduler.start()
    logger.info("✓ Daily email scheduler initialized - emails at 6:00 AM to registered users")
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
