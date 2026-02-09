from fastapi import FastAPI, HTTPException
from app.routes import health, users
from app.core.config import settings
from app.models.base import Base
from app.db.session import engine

app = FastAPI(title="AutoIntern API", version="0.1.0")

app.include_router(health.router)
app.include_router(users.router, prefix="/users", tags=["users"])

@app.on_event("startup")
async def startup_event():
    # Initialize clients and optionally create DB tables in dev
    if settings.migrate_on_start:
        # Create tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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
