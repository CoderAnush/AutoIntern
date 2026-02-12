from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoIntern API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Import routes with error handling
from app.routes import health

# Always include health router
app.include_router(health.router)

# Include initialization router
try:
    from app.routes import admin_init
    app.include_router(admin_init.router)
    logger.info("Initialization endpoints loaded")
except Exception as e:
    logger.warning(f"Failed to load initialization endpoints: {e}")

# Try to include feature routers (they may fail if external services are unavailable)
try:
    from app.routes import users
    app.include_router(users.router, prefix="/api/auth", tags=["auth"])
    logger.info("✓ Users/Auth router loaded")
except Exception as e:
    logger.warning(f"✗ Users/Auth router failed: {e}")

try:
    from app.routes import jobs
    app.include_router(jobs.router, prefix="/api", tags=["jobs"])
    logger.info("✓ Jobs router loaded")
except Exception as e:
    logger.warning(f"✗ Jobs router failed: {e}")

try:
    from app.routes import resumes
    app.include_router(resumes.router, prefix="/api", tags=["resumes"])
    logger.info("✓ Resumes router loaded")
except Exception as e:
    logger.warning(f"✗ Resumes router failed: {e}")

try:
    from app.routes import recommendations
    app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
    logger.info("✓ Recommendations router loaded")
except Exception as e:
    logger.warning(f"✗ Recommendations router failed: {e}")

try:
    from app.routes import admin
    app.include_router(admin.router, prefix="/api", tags=["admin"])
    logger.info("✓ Admin router loaded")
except Exception as e:
    logger.warning(f"✗ Admin router failed: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup."""
    logger.info("Starting application initialization...")
    try:
        from app.db.session import engine
        from app.models.models import Base

        logger.info("Creating database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema on startup: {e}", exc_info=True)


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
    return {"metrics": "unavailable"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    pass
