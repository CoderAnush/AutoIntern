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

async def upload_resume():
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

        # 2. Upload Resume
        logger.info(f"📤 Uploading resume: {RESUME_PATH}")
        if not os.path.exists(RESUME_PATH):
             logger.error("❌ Resume file not found!")
             return False

        try:
            files = {'file': ('test_resume.txt', open(RESUME_PATH, 'rb'), 'text/plain')}
            resp = await client.post(f"{BASE_URL}/resumes/upload", headers=headers, files=files)
            
            if resp.status_code == 201:
                data = resp.json()
                logger.info(f"✅ Resume Uploaded: {data.get('id')} - Skills: {len(data.get('skills', []))}")
                return True
            else:
                logger.error(f"❌ Upload Failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Upload Exception: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(upload_resume())
