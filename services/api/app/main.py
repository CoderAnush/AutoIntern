from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, users, jobs, resumes, recommendations, admin
from app.core.config import settings

app = FastAPI(title="AutoIntern API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(health.router)
app.include_router(users.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(resumes.router, prefix="/api", tags=["resumes"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    """Initialize on app startup."""
    pass


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
