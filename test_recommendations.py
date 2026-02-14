import requests
import asyncio
import sys

# Add services/api to path
sys.path.insert(0, "services/api")
from app.db.session import AsyncSessionLocal
from app.models.models import Resume
from sqlalchemy import select

async def get_test_resume_id():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Resume))
        resume = result.scalars().first()
        return resume.id if resume else None

def test_recommendations(resume_id):
    print(f"🔍 Testing Recommendations for Resume: {resume_id}")
    
    # Authenticate
    login_data = {
        "username": "test@example.com",
        "password": "password123"
    }
    # Explicitly set headers and data for OAuth2
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    resp = requests.post("http://localhost:8000/api/auth/login", data=login_data, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Login Failed: {resp.status_code} - {resp.text}")
        return
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Recommendations
    url = f"http://localhost:8000/api/recommendations/jobs-for-resume/{resume_id}"
    print(f"👉 Requesting: {url}")
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        print("\n✅ Recommendations Recieved:")
        jobs = data if isinstance(data, list) else data.get("jobs", [])
        if not jobs:
            print("  ⚠️ No jobs returned (Response format might be different)")
            print(data)
        else:
            for i, job in enumerate(jobs[:3], 1):
                # Handle different response structures
                score = job.get("match_score", job.get("score", "N/A"))
                title = job.get("title", job.get("job_title", "Unknown Job"))
                print(f"  {i}. {title} (Score: {score})")
            print(f"  ... and {len(jobs)-3} more.")
    else:
        print(f"❌ Recommendations Failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    # Get a real resume ID from DB first
    resume_id = asyncio.run(get_test_resume_id())
    if resume_id:
        test_recommendations(resume_id)
    else:
        print("❌ No resume found in database to test with.")
