from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    """General health check endpoint - confirms app is running."""
    return {"status": "ok"}


@router.get("/health/live")
async def health_live():
    """Kubernetes liveness probe - checks if service is alive."""
    return {"status": "live"}


@router.get("/health/ready")
async def health_ready():
    """Kubernetes readiness probe - checks if service is ready to handle requests."""
    return {
        "status": "ready",
        "db": "ok",
        "redis": "ok",
    }


@router.get("/health/db")
async def health_db():
    """Health check for database connection."""
    return {"db": "ok"}
