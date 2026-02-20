import asyncio
import httpx
import sys
import logging
import json

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"
EMAIL = "emergency@autointern.com"
PASSWORD = "EmergencyPass123!"

async def verify_features():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        
        # 1. Login
        logger.info("🔐 Testing Authentication...")
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
            if not token:
                logger.error("❌ No access token returned")
                return False
                
            headers = {"Authorization": f"Bearer {token}"}
            logger.info("✅ Login successful")
            
        except Exception as e:
            logger.error(f"❌ Login exception: {e}")
            return False

        # 2. Verify Jobs
        logger.info("\n💼 Testing Jobs API...")
        try:
            resp = await client.get(f"{BASE_URL}/jobs?limit=5", headers=headers)
            if resp.status_code == 200:
                jobs = resp.json()
                count = len(jobs) if isinstance(jobs, list) else len(jobs.get("items", []))
                logger.info(f"✅ Jobs Endpoint: OK ({count} jobs retrieved)")
            else:
                logger.error(f"❌ Jobs Endpoint Failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"❌ Jobs API Error: {e}")

        # 3. Verify Job Search
        logger.info("\n🔍 Testing Job Search...")
        try:
            resp = await client.get(f"{BASE_URL}/jobs/search?q=python", headers=headers)
            if resp.status_code == 200:
                results = resp.json()
                count = len(results) if isinstance(results, list) else len(results.get("items", []))
                logger.info(f"✅ Job Search: OK ({count} results for 'python')")
            else:
                logger.error(f"❌ Job Search Failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"❌ Job Search Error: {e}")

        # 4. Verify Resumes
        logger.info("\n📄 Testing Resumes API...")
        try:
            resp = await client.get(f"{BASE_URL}/resumes", headers=headers)
            if resp.status_code == 200:
                resumes = resp.json()
                count = len(resumes)
                logger.info(f"✅ Resumes Endpoint: OK ({count} resumes retrieved)")
            else:
                logger.error(f"❌ Resumes Endpoint Failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"❌ Resumes API Error: {e}")

        # 5. Verify Applications
        logger.info("\n📝 Testing Applications API...")
        try:
            resp = await client.get(f"{BASE_URL}/applications", headers=headers)
            if resp.status_code == 200:
                apps = resp.json()
                count = len(apps)
                logger.info(f"✅ Applications Endpoint: OK ({count} applications retrieved)")
            else:
                logger.error(f"❌ Applications Endpoint Failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"❌ Applications API Error: {e}")
            
        # 6. Verify Recommendations (if resume exists)
        # We need a resume ID first
        logger.info("\n🤖 Testing Recommendations API...")
        try:
            resumes_resp = await client.get(f"{BASE_URL}/resumes", headers=headers)
            if resumes_resp.status_code == 200 and len(resumes_resp.json()) > 0:
                resume_id = resumes_resp.json()[0]['id']
                rec_resp = await client.get(f"{BASE_URL}/recommendations/jobs-for-resume/{resume_id}", headers=headers)
                if rec_resp.status_code == 200:
                     logger.info(f"✅ Recommendations: OK (Generated for resume {resume_id})")
                else:
                    logger.warning(f"⚠️ Recommendations Failed: {rec_resp.status_code} - {rec_resp.text}")
            else:
                logger.warning("⚠️ No resumes found to test recommendations")
        except Exception as e:
            logger.error(f"❌ Recommendations API Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_features())
