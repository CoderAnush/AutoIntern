from fastapi import FastAPI
from app.routes import health, users

app = FastAPI(title="AutoIntern API", version="0.1.0")

app.include_router(health.router)
app.include_router(users.router, prefix="/users", tags=["users"])

@app.on_event("startup")
async def startup_event():
    # Placeholder: initialize DB, Redis, Elasticsearch clients
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Placeholder: close connections
    pass
