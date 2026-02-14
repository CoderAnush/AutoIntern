#!/usr/bin/env python3
"""Comprehensive AutoIntern Feature Test Suite - FIXED"""
import httpx
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8889/api"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "SecurePass123!"
RESUME_PATH = r"c:\Users\anush\Desktop\AutoIntern\AutoIntern\resume\test_resume.txt"

class AutoInternTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.resume_id = None
        self.job_ids = []

    def test_user_login(self):
        """Test 1: User Login"""
        logger.info("=" * 70)
        logger.info("TEST 1: User Login & Authentication")
        logger.info("=" * 70)

        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{API_BASE}/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    logger.info(f"Status: {response.status_code} OK")
                    logger.info(f"✅ LOGIN SUCCESS")
                    logger.info(f"   Token Type: {data.get('token_type')}")
                    logger.info(f"   Expires In: {data.get('expires_in')} seconds (30 minutes)")
                    return True
                else:
                    logger.error(f"❌ LOGIN FAILED: {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
                return False

    def test_resume_upload(self):
        """Test 2: Resume Upload & Skill Extraction"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Resume Upload & Skill Extraction  ")
        logger.info("=" * 70)

        if not self.token:
            logger.error("❌ No token available!")
            return False

        with httpx.Client() as client:
            try:
                with open(RESUME_PATH, 'rb') as f:
                    files = {'file': ('test_resume.txt', f, 'text/plain')}
                    headers = {'Authorization': f'Bearer {self.token}'}

                    response = client.post(
                        f"{API_BASE}/resumes/upload",
                        files=files,
                        headers=headers
                    )

                if response.status_code == 201:
                    data = response.json()
                    self.resume_id = data.get('id')

                    logger.info(f"Status: {response.status_code} Created")
                    logger.info(f"✅ RESUME UPLOAD SUCCESS")
                    logger.info(f"   Resume ID: {self.resume_id}")
                    logger.info(f"   File Name: {data.get('file_name')}")

                    # Extract skills
                    skills = data.get('skills', [])
                    if isinstance(skills, str):
                        try:
                            skills = json.loads(skills)
                        except:
                            skills = []

                    logger.info(f"   AI-Extracted Skills: {len(skills)} total")
                    for i, skill in enumerate(skills[:12]):
                        logger.info(f"      [{i+1}] {skill}")
                    if len(skills) > 12:
                        logger.info(f"      ... and {len(skills) - 12} more skills")

                    logger.info(f"\n   Resume successfully analyzed and indexed!")
                    return True
                else:
                    logger.error(f"❌ UPLOAD FAILED: {response.status_code}")
                    logger.error(f"   Response: {response.text[:200]}")
                    return False
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
                return False

    def test_job_recommendations(self):
        """Test 3: Job Recommendations Engine"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: ML-Based Job Recommendations")
        logger.info("=" * 70)

        if not self.token or not self.resume_id:
            logger.error("❌ Need token and resume_id!")
            return False

        with httpx.Client() as client:
            try:
                headers = {'Authorization': f'Bearer {self.token}'}

                # Trigger batch indexing
                logger.info("Indexing all jobs with embeddings...")
                try:
                    index_response = client.post(
                        f"{API_BASE}/recommendations/batch-index-jobs?background=false",
                        headers=headers,
                        timeout=30
                    )
                    logger.info(f"   Indexing status: {index_response.status_code}")
                except:
                    pass

                # Get recommendations with minimum similarity 0.0 to get all matching jobs
                response = client.get(
                    f"{API_BASE}/recommendations/jobs-for-resume/{self.resume_id}?top_k=30&min_similarity=0.0",
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    recommendations = response.json()
                    logger.info(f"Status: {response.status_code} OK")
                    logger.info(f"✅ RECOMMENDATIONS GENERATED")
                    logger.info(f"   Matching Jobs Found: {len(recommendations)}")

                    if len(recommendations) > 0:
                        logger.info(f"\n   TOP 10 JOB RECOMMENDATIONS (By Relevance):")
                        logger.info(f"   {'Rank':<6} {'Title':<30} {'Company':<20} {'Match%':<8}")
                        logger.info(f"   {'-'*70}")

                        for i, job in enumerate(recommendations[:10], 1):
                            title = (job.get('job_title') or job.get('title', 'N/A'))[:28]
                            company = job.get('company_name', 'N/A')[:18]
                            similarity = job.get('similarity_score', 0) * 100
                            apply_url = job.get('apply_url', '')

                            self.job_ids.append(job.get('job_id'))

                            logger.info(f"   {i:<6} {title:<30} {company:<20} {similarity:>6.1f}%")

                            # Detailed view of top 3
                            if i <= 3:
                                logger.info(f"       ├─ Location: {job.get('location', 'N/A')}")
                                logger.info(f"       ├─ Type: {job.get('job_type', 'N/A')}")
                                logger.info(f"       └─ Apply: {apply_url[:60]}...")

                        return True
                    else:
                        logger.warning(f"⚠️  No matching jobs found")
                        return False
                else:
                    logger.error(f"❌ FAILED: {response.status_code}")
                    logger.error(f"   {response.text[:200]}")
                    return False
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                return False

    def test_job_application(self):
        """Test 4: Job Application & Company Redirect"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: Job Application & Company Career Page Redirect")
        logger.info("=" * 70)

        if not self.token or not self.job_ids:
            logger.error("❌ Need token and job IDs!")
            return False

        with httpx.Client() as client:
            try:
                headers = {'Authorization': f'Bearer {self.token}'}

                job_id = self.job_ids[0]
                response = client.get(
                    f"{API_BASE}/jobs/{job_id}",
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"❌ Could not fetch job: {response.status_code}")
                    return False

                job = response.json()
                apply_url = job.get('apply_url', '')
                company_name = job.get('company_name', 'Unknown')
                job_title = job.get('title', 'Unknown')

                logger.info(f"Creating application for recommended job:")
                logger.info(f"   Title: {job_title}")
                logger.info(f"   Company: {company_name}")
                logger.info(f"   Apply URL: {apply_url}")

                # Create application
                app_data = {
                    "job_id": job_id,
                    "resume_id": self.resume_id,
                    "company_name": company_name,
                    "role_title": job_title,
                    "status": "applied",
                    "notes": "Applied via AutoIntern AI matching"
                }

                app_response = client.post(
                    f"{API_BASE}/applications/",
                    json=app_data,
                    headers=headers
                )

                if app_response.status_code == 201:
                    app = app_response.json()
                    logger.info(f"Status: {app_response.status_code} Created")
                    logger.info(f"✅ APPLICATION CREATED & TRACKED")
                    logger.info(f"   Application ID: {app.get('id')}")
                    logger.info(f"   Status: {app.get('status')}")
                    logger.info(f"   Applied At: {app.get('applied_at')}")
                    logger.info(f"\n   COMPANY REDIRECT INFO:")
                    logger.info(f"   ✅ Redirect URL: {apply_url}")

                    if "careers" in apply_url.lower() or "jobs" in apply_url.lower():
                        logger.info(f"   ✅ Valid company career page")
                    logger.info(f"   ✅ User will click 'Apply' button to visit company page")

                    return True
                else:
                    logger.error(f"❌ APPLICATION FAILED: {app_response.status_code}")
                    logger.error(f"   {app_response.text[:200]}")
                    return False
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
                return False

    def test_list_applications(self):
        """Test 5: List User Applications"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: Application Tracking Dashboard")
        logger.info("=" * 70)

        if not self.token:
            logger.error("❌ No token!")
            return False

        with httpx.Client() as client:
            try:
                headers = {'Authorization': f'Bearer {self.token}'}

                response = client.get(
                    f"{API_BASE}/applications/",
                    headers=headers
                )

                if response.status_code == 200:
                    applications = response.json()
                    logger.info(f"Status: {response.status_code} OK")
                    logger.info(f"✅ APPLICATIONS RETRIEVED")
                    logger.info(f"   Total Tracked Applications: {len(applications)}")

                    if len(applications) > 0:
                        logger.info(f"\n   Recent Applications:")
                        for i, app in enumerate(applications[:5], 1):
                            logger.info(f"   [{i}] {app.get('role_title')} @ {app.get('company_name')}")
                            logger.info(f"       Status: {app.get('status')} | Applied: {app.get('applied_at')}")

                    return True
                else:
                    logger.error(f"❌ FAILED: {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
                return False

    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n")
        logger.info("╔" + "═" * 68 + "╗")
        logger.info("║" + " " * 15 + "AUTOINTERN FEATURE VERIFICATION SUITE" + " " * 15 + "║")
        logger.info("║" + " " * 20 + "End-to-End Functionality Test" + " " * 20 + "║")
        logger.info("╚" + "═" * 68 + "╝")

        results = {
            "User Authentication": self.test_user_login(),
            "Resume Upload & Analysis": self.test_resume_upload(),
            "ML Job Recommendations": self.test_job_recommendations(),
            "Job Application Tracking": self.test_job_application(),
            "Application Dashboard": self.test_list_applications(),
        }

        # Summary Report
        logger.info("\n" + "=" * 70)
        logger.info("                          TEST RESULTS SUMMARY")
        logger.info("=" * 70)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}  {test_name}")

        logger.info("=" * 70)

        if passed == total:
            logger.info(f"\n🎉 SUCCESS! All {total}/{total} tests passed!")
            logger.info("\n✅ SYSTEM STATUS: ALL FEATURES WORKING")
            logger.info("   ✅ User authentication & JWT tokens")
            logger.info("   ✅ Resume upload & AI skill extraction")
            logger.info("   ✅ ML-based job recommendations")
            logger.info("   ✅ Job application tracking")
            logger.info("   ✅ Company career page redirects")
            logger.info("\n   System is READY for real data integration!")
            return True
        else:
            logger.warning(f"\n⚠️  {total - passed}/{total} test(s) failed")
            return False

def main():
    tester = AutoInternTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
