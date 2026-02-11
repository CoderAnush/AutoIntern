from fastapi import FastAPI

# Absolute minimal - nothing else
app = FastAPI(title="AutoIntern API", version="0.1.0")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
