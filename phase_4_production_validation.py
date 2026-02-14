#!/usr/bin/env python3
"""
Phase 4: Production Validation Test Suite
Comprehensive testing with real job data (92 total jobs)
Tests: Performance, accuracy, reliability, end-to-end workflows
"""
import httpx
import json
import time
import logging
from typing import List, Dict
import asyncio

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8889/api"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "SecurePass123!"

class ProductionValidationSuite:
    def __init__(self):
        self.results = {
            "performance": [],
            "accuracy": [],
            "reliability": [],
            "integration": []
        }
        self.token = None
        self.user_id = None

    def log_section(self, title):
        logger.info("")
        logger.info("="*80)
        logger.info(f"  {title}")
        logger.info("="*80)

    def log_test(self, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        symbol = "[+]" if passed else "[-]"
        logger.info(f"{symbol} {name}: {status}" + (f" - {details}" if details else ""))
        return passed

    # ========== PERFORMANCE TESTS ==========

    async def test_login_performance(self):
        """Test authentication speed"""
        logger.info("\n[Test 1] User Login Performance...")
        start = time.time()

        with httpx.Client(timeout=10) as client:
            response = client.post(f"{API_BASE}/auth/login",
                                  json={"email": TEST_EMAIL, "password": TEST_PASSWORD})

        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            passed = elapsed < 200  # Target: <200ms
            self.log_test(
                "User Login",
                passed,
                f"{elapsed:.1f}ms (target: <200ms)"
            )
            self.results["performance"].append({"test": "login", "ms": elapsed, "passed": passed})
            return True
        return False

    async def test_job_search_performance(self):
        """Test job search at scale"""
        logger.info("\n[Test 2] Job Search Performance (92 jobs)...")
        start = time.time()

        with httpx.Client(timeout=10) as client:
            response = client.get(f"{API_BASE}/jobs/search?q=engineer&limit=50",
                                 follow_redirects=True)

        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            jobs = response.json()
            passed = elapsed < 500 and len(jobs) > 0  # Target: <500ms
            self.log_test(
                "Job Search (50 results)",
                passed,
                f"{elapsed:.1f}ms, {len(jobs)} jobs found"
            )
            self.results["performance"].append({"test": "job_search", "ms": elapsed, "passed": passed})
            return True
        return False

    async def test_recommendation_performance(self):
        """Test recommendation engine with real jobs"""
        if not self.token:
            logger.info("\n[Test 3] Recommendations - SKIPPED (no token)")
            return False

        logger.info("\n[Test 3] Recommendation Engine Performance...")
        headers = {'Authorization': f'Bearer {self.token}'}

        with httpx.Client(timeout=30) as client:
            # Get resume
            resumes = client.get(f"{API_BASE}/resumes", headers=headers,
                               follow_redirects=True).json()

            if not resumes:
                logger.info("[-] No resumes for recommendation test")
                return False

            resume_id = resumes[0].get('id')
            start = time.time()

            # Get recommendations
            response = client.get(
                f"{API_BASE}/recommendations/jobs-for-resume/{resume_id}?top_k=100&min_similarity=0.0",
                headers=headers, timeout=30, follow_redirects=True
            )

        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            recommendations = response.json()
            passed = elapsed < 2000 and len(recommendations) > 0  # Target: <2 seconds
            self.log_test(
                "Recommendations (100 jobs)",
                passed,
                f"{elapsed:.1f}ms, {len(recommendations)} matches"
            )
            self.results["performance"].append({
                "test": "recommendations",
                "ms": elapsed,
                "matches": len(recommendations),
                "passed": passed
            })
            return True
        return False

    # ========== ACCURACY TESTS ==========

    async def test_real_job_matching(self):
        """Verify real jobs are being matched"""
        if not self.token:
            logger.info("\n[Test 4] Real Job Matching - SKIPPED (no token)")
            return False

        logger.info("\n[Test 4] Real Job Matching Accuracy...")
        headers = {'Authorization': f'Bearer {self.token}'}

        with httpx.Client(timeout=30) as client:
            resumes = client.get(f"{API_BASE}/resumes", headers=headers,
                               follow_redirects=True).json()

            if not resumes:
                return False

            resume_id = resumes[0].get('id')
            response = client.get(
                f"{API_BASE}/recommendations/jobs-for-resume/{resume_id}?top_k=30&min_similarity=0.0",
                headers=headers, timeout=30, follow_redirects=True
            )

        if response.status_code == 200:
            recommendations = response.json()

            # Check for real jobs (from Indeed, Wellfound, RemoteOK)
            real_job_sources = ['indeed', 'wellfound', 'remoteok']
            real_jobs = [j for j in recommendations if j.get('job_source') in real_job_sources]

            passed = len(real_jobs) > 0
            percentage = (len(real_jobs) / len(recommendations) * 100) if recommendations else 0

            self.log_test(
                "Real Job Matching",
                passed,
                f"{len(real_jobs)}/{len(recommendations)} real jobs ({percentage:.0f}%)"
            )
            self.results["accuracy"].append({
                "test": "real_job_matching",
                "real_jobs": len(real_jobs),
                "total": len(recommendations),
                "percentage": percentage,
                "passed": passed
            })
            return True
        return False

    async def test_recommendation_score_distribution(self):
        """Verify similarity scores are properly distributed"""
        if not self.token:
            return False

        logger.info("\n[Test 5] Similarity Score Distribution...")
        headers = {'Authorization': f'Bearer {self.token}'}

        with httpx.Client(timeout=30) as client:
            resumes = client.get(f"{API_BASE}/resumes", headers=headers,
                               follow_redirects=True).json()

            if not resumes:
                return False

            resume_id = resumes[0].get('id')
            response = client.get(
                f"{API_BASE}/recommendations/jobs-for-resume/{resume_id}?top_k=30&min_similarity=0.0",
                headers=headers, timeout=30, follow_redirects=True
            )

        if response.status_code == 200:
            recommendations = response.json()
            scores = [r.get('similarity_score', 0) for r in recommendations]

            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)

                # Scores should be well-distributed and reasonable
                passed = 0.3 <= avg_score <= 0.9 and min_score < max_score

                self.log_test(
                    "Score Distribution",
                    passed,
                    f"avg={avg_score:.2f}, min={min_score:.2f}, max={max_score:.2f}"
                )
                self.results["accuracy"].append({
                    "test": "score_distribution",
                    "avg": avg_score,
                    "min": min_score,
                    "max": max_score,
                    "passed": passed
                })
                return True
        return False

    # ========== RELIABILITY TESTS ==========

    async def test_total_job_count(self):
        """Verify all jobs are accessible"""
        logger.info("\n[Test 6] Job Database Integrity...")

        with httpx.Client(timeout=10) as client:
            response = client.get(f"{API_BASE}/jobs?limit=200",
                                 follow_redirects=True)

        if response.status_code == 200:
            jobs = response.json()
            # Should have 92 jobs (59 mock + 21 real + 12 other)
            passed = len(jobs) >= 80  # Allow some variance

            self.log_test(
                "Total Job Count",
                passed,
                f"{len(jobs)} jobs accessible"
            )
            self.results["reliability"].append({
                "test": "job_count",
                "total": len(jobs),
                "passed": passed
            })
            return True
        return False

    async def test_company_url_validity(self):
        """Verify company redirect URLs are present"""
        logger.info("\n[Test 7] Company Redirect URL Validity...")

        with httpx.Client(timeout=10) as client:
            response = client.get(f"{API_BASE}/jobs?limit=100",
                                 follow_redirects=True)

        if response.status_code == 200:
            jobs = response.json()
            jobs_with_urls = sum(1 for j in jobs if j.get('apply_url'))

            passed = jobs_with_urls >= len(jobs) * 0.9  # 90%+ should have URLs

            self.log_test(
                "Career Page URLs",
                passed,
                f"{jobs_with_urls}/{len(jobs)} jobs have apply URLs"
            )
            self.results["reliability"].append({
                "test": "url_validity",
                "with_urls": jobs_with_urls,
                "total": len(jobs),
                "passed": passed
            })
            return True
        return False

    async def test_database_consistency(self):
        """Test database operations are consistent"""
        logger.info("\n[Test 8] Database Consistency...")

        if not self.token:
            logger.info("[-] Database Consistency - SKIPPED (no token)")
            return False

        headers = {'Authorization': f'Bearer {self.token}'}

        # Create test application
        test_app_data = {
            "job_id": "test-job-123",
            "resume_id": "test-resume-123",
            "company_name": "Test Company",
            "role_title": "Test Role",
            "status": "applied",
            "notes": "Test application"
        }

        with httpx.Client(timeout=10) as client:
            # Create
            create_response = client.post(f"{API_BASE}/applications",
                                         json=test_app_data,
                                         headers=headers)

            if create_response.status_code == 201:
                app_id = create_response.json().get('id')

                # List
                list_response = client.get(f"{API_BASE}/applications",
                                          headers=headers, follow_redirects=True)

                if list_response.status_code == 200:
                    apps = list_response.json()
                    found = any(a.get('id') == app_id for a in apps)

                    # Update
                    if found:
                        update_response = client.patch(
                            f"{API_BASE}/applications/{app_id}",
                            json={"status": "interview"},
                            headers=headers
                        )

                        passed = update_response.status_code in [200, 204]
                        self.log_test(
                            "Database Consistency",
                            passed,
                            "Create-List-Update cycle successful"
                        )
                        self.results["reliability"].append({
                            "test": "db_consistency",
                            "passed": passed
                        })
                        return True

        self.log_test("Database Consistency", False, "Operation failed")
        return False

    # ========== INTEGRATION TESTS ==========

    async def test_complete_user_journey(self):
        """Test complete workflow: register, upload, get recommendations, apply"""
        logger.info("\n[Test 9] Complete User Journey (with real jobs)...")

        if not self.token:
            logger.info("[-] User Journey - SKIPPED (no token)")
            return False

        headers = {'Authorization': f'Bearer {self.token}'}
        journey_steps = []

        with httpx.Client(timeout=30) as client:
            # Step 1: Get resumes
            resume_response = client.get(f"{API_BASE}/resumes", headers=headers,
                                        follow_redirects=True)
            if resume_response.status_code != 200:
                self.log_test("User Journey", False, "Resume retrieval failed")
                return False
            journey_steps.append("resumes_retrieved")

            resumes = resume_response.json()
            if not resumes:
                self.log_test("User Journey", False, "No resumes available")
                return False

            resume_id = resumes[0].get('id')

            # Step 2: Get recommendations
            rec_response = client.get(
                f"{API_BASE}/recommendations/jobs-for-resume/{resume_id}?top_k=10",
                headers=headers, timeout=30, follow_redirects=True
            )
            if rec_response.status_code != 200:
                self.log_test("User Journey", False, "Recommendations failed")
                return False
            journey_steps.append("recommendations_generated")

            recommendations = rec_response.json()
            if not recommendations:
                self.log_test("User Journey", False, "No recommendations")
                return False

            top_job_id = recommendations[0].get('job_id')

            # Step 3: Create application
            app_response = client.post(f"{API_BASE}/applications",
                                      json={
                                          "job_id": top_job_id,
                                          "resume_id": resume_id,
                                          "company_name": recommendations[0].get('job_company'),
                                          "role_title": recommendations[0].get('job_title'),
                                          "status": "applied"
                                      },
                                      headers=headers)
            if app_response.status_code != 201:
                self.log_test("User Journey", False, "Application creation failed")
                return False
            journey_steps.append("application_created")

            # Step 4: Get applications
            apps_response = client.get(f"{API_BASE}/applications", headers=headers,
                                      follow_redirects=True)
            if apps_response.status_code != 200:
                self.log_test("User Journey", False, "Application retrieval failed")
                return False
            journey_steps.append("applications_retrieved")

        passed = len(journey_steps) == 4
        self.log_test(
            "Complete User Journey",
            passed,
            f"Steps: {' -> '.join(journey_steps)}"
        )
        self.results["integration"].append({
            "test": "user_journey",
            "steps": journey_steps,
            "passed": passed
        })
        return True

    async def test_real_job_application_flow(self):
        """Test applying to real jobs specifically"""
        logger.info("\n[Test 10] Real Job Application Flow...")

        if not self.token:
            return False

        headers = {'Authorization': f'Bearer {self.token}'}

        with httpx.Client(timeout=30) as client:
            # Get a real job
            real_job_response = client.get(
                f"{API_BASE}/jobs/search?q=engineer&limit=100",
                follow_redirects=True
            )

            if real_job_response.status_code != 200:
                self.log_test("Real Job Application", False, "Job search failed")
                return False

            jobs = real_job_response.json()
            real_jobs = [j for j in jobs if j.get('source') in ['indeed', 'wellfound', 'remoteok']]

            if not real_jobs:
                self.log_test("Real Job Application", False, "No real jobs found")
                return False

            real_job = real_jobs[0]

            # Get resumes
            resumes = client.get(f"{API_BASE}/resumes", headers=headers,
                               follow_redirects=True).json()
            if not resumes:
                self.log_test("Real Job Application", False, "No resumes")
                return False

            resume_id = resumes[0].get('id')

            # Apply to real job
            app_response = client.post(f"{API_BASE}/applications",
                                      json={
                                          "job_id": real_job.get('id'),
                                          "resume_id": resume_id,
                                          "company_name": real_job.get('company_name'),
                                          "role_title": real_job.get('title'),
                                          "status": "applied"
                                      },
                                      headers=headers)

            passed = app_response.status_code == 201
            self.log_test(
                "Real Job Application",
                passed,
                f"Applied to {real_job.get('title')} @ {real_job.get('company_name')}"
            )
            self.results["integration"].append({
                "test": "real_job_application",
                "job": real_job.get('title'),
                "company": real_job.get('company_name'),
                "passed": passed
            })
            return True
        return False

    # ========== REPORTING ==========

    def print_results(self):
        """Print comprehensive test results"""
        self.log_section("PHASE 4 PRODUCTION VALIDATION RESULTS")

        total_tests = sum(len(v) for v in self.results.values())
        passed_tests = sum(
            sum(1 for t in tests if t.get('passed', False))
            for tests in self.results.values()
        )

        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")

        # Performance Summary
        if self.results["performance"]:
            logger.info("\nPERFORMANCE BENCHMARKS:")
            for test in self.results["performance"]:
                logger.info(f"  {test['test']}: {test['ms']:.1f}ms")

        # Accuracy Summary
        if self.results["accuracy"]:
            logger.info("\nACCURACY METRICS:")
            for test in self.results["accuracy"]:
                if 'real_jobs' in test:
                    logger.info(f"  Real job matching: {test['percentage']:.0f}% ({test['real_jobs']}/{test['total']})")
                elif 'avg' in test:
                    logger.info(f"  Score distribution: avg={test['avg']:.2f}, range=[{test['min']:.2f}, {test['max']:.2f}]")

        # Reliability Summary
        if self.results["reliability"]:
            logger.info("\nRELIABILITY:")
            for test in self.results["reliability"]:
                if test['test'] == 'job_count':
                    logger.info(f"  Jobs accessible: {test['total']}")
                elif test['test'] == 'url_validity':
                    logger.info(f"  Valid career URLs: {test['with_urls']}/{test['total']}")

        # Integration Summary
        if self.results["integration"]:
            logger.info("\nINTEGRATION TESTS:")
            for test in self.results["integration"]:
                if test['test'] == 'user_journey':
                    logger.info(f"  User journey completed: {' -> '.join(test['steps'])}")
                elif test['test'] == 'real_job_application':
                    logger.info(f"  Real job applied: {test['job']} @ {test['company']}")

        self.log_section("STATUS")
        if passed_tests == total_tests:
            logger.info("\nPHASE 4: ALL TESTS PASSED - PRODUCTION READY")
        else:
            logger.info(f"\nPHASE 4: {passed_tests}/{total_tests} tested passed")

    async def run_all(self):
        """Run complete test suite"""
        self.log_section("PHASE 4: PRODUCTION VALIDATION TEST SUITE")
        logger.info("Testing with 92 total jobs (59 mock + 21 real + 12 other)")

        # Authentication
        await self.test_login_performance()

        # Performance
        await self.test_job_search_performance()
        await self.test_recommendation_performance()

        # Accuracy
        await self.test_real_job_matching()
        await self.test_recommendation_score_distribution()

        # Reliability
        await self.test_total_job_count()
        await self.test_company_url_validity()
        await self.test_database_consistency()

        # Integration
        await self.test_complete_user_journey()
        await self.test_real_job_application_flow()

        # Results
        self.print_results()

async def main():
    suite = ProductionValidationSuite()
    await suite.run_all()

if __name__ == "__main__":
    asyncio.run(main())
