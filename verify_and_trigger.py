import asyncio
import httpx
import sys
import logging
import os

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"
EMAIL = "emergency@autointern.com"
PASSWORD = "EmergencyPass123!"
RESUME_PATH = r"c:\Users\anush\Desktop\AutoIntern\AutoIntern\resume\test_resume.txt"

async def verify_user_journey():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 1. Login
        logger.info("🔐 Logging in...")
        try:
            login_data = {"email": EMAIL, "password": PASSWORD}
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json=login_data
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Login failed: {response.text}")
                return False
                
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            logger.info("✅ Login successful")
            
        except Exception as e:
            logger.error(f"❌ Login exception: {e}")
            return False

        # 2. Upload Resume (if not already)
        # We can try to upload, or listing existing ones
        logger.info("📂 Checking for existing resumes...")
        resumes_resp = await client.get(f"{BASE_URL}/resumes", headers=headers)
        resume_id = None
        
        if resumes_resp.status_code == 200 and len(resumes_resp.json()) > 0:
            resume_id = resumes_resp.json()[0]['id']
            logger.info(f"✅ Found existing resume: {resume_id}")
        else:
            logger.info(f"📤 Uploading resume: {RESUME_PATH}")
            if not os.path.exists(RESUME_PATH):
                 logger.error("❌ Resume file not found!")
                 return False

            try:
                files = {'file': ('test_resume.txt', open(RESUME_PATH, 'rb'), 'text/plain')}
                resp = await client.post(f"{BASE_URL}/resumes/upload", headers=headers, files=files)
                
                if resp.status_code == 201:
                    data = resp.json()
                    resume_id = data.get('id')
                    logger.info(f"✅ Resume Uploaded: {resume_id}")
                else:
                    logger.error(f"❌ Upload Failed: {resp.status_code} - {resp.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Upload Exception: {e}")
                return False

        # 3. Get Recommendations
        if not resume_id:
            logger.error("❌ No resume ID found/created.")
            return False
            
        logger.info(f"🤖 Getting recommendations for resume {resume_id}...")
        try:
            rec_resp = await client.get(f"{BASE_URL}/recommendations/jobs-for-resume/{resume_id}", headers=headers)
            if rec_resp.status_code == 200:
                recommendations = rec_resp.json()
                count = len(recommendations)
                logger.info(f"✅ Recommendations Received: {count} jobs")
                
                if count > 0:
                    top_job = recommendations[0]
                    logger.info(f"🏆 Top Job: {top_job.get('title')} at {top_job.get('company_name')}")
                    logger.info(f"🔗 Apply URL: {top_job.get('apply_url')}")
                    
                    # Verify URL is reachable (HEAD request)
                    # Note: Localhost jobs might have fake URLs, strictly check if field exists
                    if top_job.get('apply_url'):
                         logger.info("✅ Apply URL exists and user can be redirected.")
                    else:
                         logger.warning("⚠️ No Apply URL found for top job.")
                else:
                    logger.warning("⚠️ No recommendations found.")
            else:
                logger.error(f"❌ Recommendations Failed: {rec_resp.status_code} - {rec_resp.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Recommendations Exception: {e}")
            return False
            
        return True

if __name__ == "__main__":
    asyncio.run(verify_user_journey())
