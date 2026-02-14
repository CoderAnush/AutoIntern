"""
Mock API server for local development and testing.
Provides basic endpoints without ML dependencies.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import json
from datetime import datetime, timedelta
import secrets

app = FastAPI(title="AutoIntern Mock API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
users_db = {}
tokens = {}
jobs_db = {
    "job1": {
        "id": "job1",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "description": "Looking for experienced Python developer with FastAPI experience",
        "url": "https://example.com/jobs/1"
    },
    "job2": {
        "id": "job2",
        "title": "Frontend Engineer",
        "company": "StartupXYZ",
        "location": "Remote",
        "description": "React/TypeScript frontend engineer needed",
        "url": "https://example.com/jobs/2"
    },
    "job3": {
        "id": "job3",
        "title": "Full Stack Developer",
        "company": "WebServices Inc",
        "location": "New York, NY",
        "description": "Full stack developer with Python and React skills",
        "url": "https://example.com/jobs/3"
    }
}
resumes_db = {}

# ==================== Models ====================

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class JobOut(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    url: Optional[str] = None

class ResumeOut(BaseModel):
    id: str
    filename: str
    user_id: str
    created_at: str
    file_url: Optional[str] = None

class RecommendationResult(BaseModel):
    job_id: str
    similarity_score: float
    match_percentage: float

class ResumeQualityScore(BaseModel):
    resume_id: str
    overall_score: float
    categories: dict

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# ==================== Helper Functions ====================

def generate_token():
    return secrets.token_urlsafe(32)

def get_current_user(token: Optional[str] = None):
    if not token or token not in tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return tokens[token]

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mock-api"}

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_id = secrets.token_urlsafe(8)
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": user_data.password,  # In production, this would be hashed
        "full_name": user_data.full_name,
        "created_at": datetime.utcnow().isoformat()
    }
    users_db[user_data.email] = user

    return UserResponse(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        created_at=user["created_at"]
    )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user and get tokens."""
    user = users_db.get(credentials.email)

    if not user or user["password"] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = generate_token()
    refresh_token = generate_token()

    tokens[access_token] = user["id"]
    tokens[refresh_token] = user["id"]

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/api/auth/refresh-token", response_model=TokenResponse)
async def refresh_access_token(data: dict):
    """Refresh access token."""
    refresh_token = data.get("refresh_token")

    if refresh_token not in tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token = generate_token()
    tokens[access_token] = tokens[refresh_token]

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_endpoint(authorization: Optional[str] = None):
    """Get current user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    token = authorization.replace("Bearer ", "")
    user_id = get_current_user(token)

    # Find user by id
    for user in users_db.values():
        if user["id"] == user_id:
            return UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user.get("full_name"),
                created_at=user["created_at"]
            )

    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/auth/logout")
async def logout():
    """Logout user."""
    return {"detail": "Logged out successfully"}

@app.post("/api/users/change-password")
async def change_password(data: PasswordChange, authorization: Optional[str] = None):
    """Change user password."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    user_id = get_current_user(token)

    # Find user and validate current password
    user = None
    for u in users_db.values():
        if u["id"] == user_id:
            user = u
            break

    if not user or user["password"] != data.current_password:
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Update password
    user["password"] = data.new_password
    return {"detail": "Password changed successfully"}

# ==================== Jobs Endpoints ====================

@app.get("/api/jobs", response_model=list)
async def list_jobs(limit: int = 20, offset: int = 0):
    """List all jobs."""
    job_list = list(jobs_db.values())
    return job_list[offset:offset+limit]

@app.get("/api/jobs/search", response_model=list)
async def search_jobs(q: Optional[str] = None, location: Optional[str] = None, limit: int = 20):
    """Search jobs."""
    search_term = q or ""

    if not search_term:
        return list(jobs_db.values())[:limit]

    results = [
        job for job in jobs_db.values()
        if search_term.lower() in job["title"].lower() or search_term.lower() in job["description"].lower()
    ]

    if location:
        results = [job for job in results if location.lower() in job["location"].lower()]

    return results[:limit]

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job by ID."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs_db[job_id]

# ==================== Resumes Endpoints ====================

@app.post("/api/resumes/upload", response_model=ResumeOut)
async def upload_resume(authorization: Optional[str] = None, file = None):
    """Upload resume file."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    user_id = get_current_user(token)

    resume_id = secrets.token_urlsafe(8)
    resume = {
        "id": resume_id,
        "filename": "resume.pdf",
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "file_url": f"/resumes/{resume_id}/file"
    }
    resumes_db[resume_id] = resume

    return ResumeOut(**resume)

@app.get("/api/resumes", response_model=list)
async def list_resumes(limit: int = 10, offset: int = 0, authorization: Optional[str] = None):
    """List user's resumes."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "")
    user_id = get_current_user(token)

    user_resumes = [r for r in resumes_db.values() if r["user_id"] == user_id]
    return [ResumeOut(**r) for r in user_resumes[offset:offset+limit]]

@app.get("/api/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume by ID."""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")

    return ResumeOut(**resumes_db[resume_id])

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete resume."""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")

    del resumes_db[resume_id]
    return {"detail": "Resume deleted"}

# ==================== Recommendations Endpoints ====================

@app.get("/api/recommendations/jobs-for-resume/{resume_id}", response_model=list)
async def get_recommended_jobs(
    resume_id: str,
    min_similarity: float = 0.5,
    top_k: int = 20
):
    """Get jobs recommended for a resume."""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Return mock recommendations
    recommendations = []
    for job_id, job in list(jobs_db.items())[:top_k]:
        recommendations.append({
            "job_id": job_id,
            "similarity_score": 0.75,
            "match_percentage": 75.0
        })

    return recommendations

@app.get("/api/recommendations/resumes-for-job/{job_id}", response_model=list)
async def get_recommended_resumes(
    job_id: str,
    min_similarity: float = 0.5,
    top_k: int = 20
):
    """Get resumes recommended for a job."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    # Return mock recommendations
    recommendations = []
    for resume_id, resume in list(resumes_db.items())[:top_k]:
        recommendations.append({
            "resume_id": resume_id,
            "similarity_score": 0.75,
            "match_percentage": 75.0
        })

    return recommendations

@app.get("/api/recommendations/resume-quality/{resume_id}", response_model=ResumeQualityScore)
async def get_resume_quality(resume_id: str):
    """Get resume quality scores."""
    if resume_id not in resumes_db:
        raise HTTPException(status_code=404, detail="Resume not found")

    return ResumeQualityScore(
        resume_id=resume_id,
        overall_score=0.85,
        categories={
            "format": 0.9,
            "content": 0.8,
            "keywords": 0.75,
            "structure": 0.85
        }
    )

# ==================== Initialization (seed data) ====================

@app.post("/api/init/seed-jobs")
async def seed_jobs():
    """Seed mock job data."""
    sample_jobs = [
        {
            "id": "job1",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "description": "Looking for experienced Python developer with FastAPI experience",
            "url": "https://example.com/jobs/1"
        },
        {
            "id": "job2",
            "title": "Frontend Engineer",
            "company": "StartupXYZ",
            "location": "Remote",
            "description": "React/TypeScript frontend engineer needed",
            "url": "https://example.com/jobs/2"
        },
        {
            "id": "job3",
            "title": "Full Stack Developer",
            "company": "WebServices Inc",
            "location": "New York, NY",
            "description": "Full stack developer with Python and React skills",
            "url": "https://example.com/jobs/3"
        }
    ]

    for job in sample_jobs:
        jobs_db[job["id"]] = job

    return {"detail": f"Seeded {len(sample_jobs)} jobs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
