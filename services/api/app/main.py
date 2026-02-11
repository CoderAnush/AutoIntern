from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, users, resumes, recommendations, emails
from app.core.config import settings
from app.models.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.middleware.security_headers import add_security_headers
from app.middleware.request_logging import add_request_logging
from app.services.monitoring import get_health_monitor

app = FastAPI(title="AutoIntern API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add Phase 8 Security Hardening middleware
add_security_headers(app)
add_request_logging(app, AsyncSessionLocal)

app.include_router(health.router)
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(__import__('app.routes.jobs').routes.router, prefix="", tags=["jobs"])  # register jobs router
app.include_router(resumes.router, prefix="", tags=["resumes"])  # resume upload and management
app.include_router(recommendations.router, prefix="", tags=["recommendations"])  # job recommendations and quality scoring
app.include_router(emails.router, prefix="/users/me", tags=["emails"])  # email preferences and logs (Phase 7)
app.include_router(__import__('app.routes.admin').routes.router, prefix="", tags=["admin"])  # admin endpoints for DLQ inspection and management

@app.on_event("startup")
async def startup_event():
    # Initialize clients and optionally create DB tables in dev
    if settings.migrate_on_start:
        # Create tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    # Simple request counter middleware; records method, path, and status
    try:
        from app.metrics import REQUEST_COUNT
    except Exception:
        REQUEST_COUNT = None

    response = await call_next(request)

    if REQUEST_COUNT is not None:
        try:
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=str(response.status_code)).inc()
        except Exception:
            pass

    return response


@app.get("/metrics")
async def metrics():
    try:
        from app.metrics import metrics_response

        data, content_type = metrics_response()
        from fastapi.responses import Response

        return Response(content=data, media_type=content_type)
    except Exception:
        return {"error": "metrics unavailable"}

@app.on_event("shutdown")
async def shutdown_event():
    # Placeholder: close connections
    pass

@app.get("/health/db")
async def health_db():
    # Try a minimal DB connect to ensure migrations/DB readiness
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"db": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"db unavailable: {exc}")


# Phase 8 Health Monitoring Endpoints
@app.get("/health")
async def health_check():
    """General health check endpoint."""
    monitor = await get_health_monitor()
    status = await monitor.get_health_status()

    status_code = 200 if status["status"] == "healthy" else 503
    return status if status_code == 200 else {"status": status["status"], "checks": status}


@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe - checks if service is alive."""
    return {"status": "live"}


@app.get("/health/ready")
async def health_ready():
    """Kubernetes readiness probe - checks if service is ready to handle requests."""
    monitor = await get_health_monitor()
    db_ok = await monitor.check_database()
    redis_ok = await monitor.check_redis()

    status_code = 200 if (db_ok and redis_ok) else 503

    response = {
        "status": "ready" if (db_ok and redis_ok) else "not_ready",
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }

    return response


@app.get("/metrics/summary")
async def metrics_summary():
    """Get performance metrics summary."""
    monitor = await get_health_monitor()
    metrics = await monitor.get_metrics()
    return metrics
