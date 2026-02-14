#!/usr/bin/env python3
"""
AutoIntern Feature Testing Script
Tests authentication, resume upload, job browsing, and recommendations
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPass123!"

class AutoInternTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.resume_id = None
        self.job_ids = []
        
    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def test_login(self):
        """Test user authentication"""
        self.print_section("1. Testing Authentication")
        
        url = f"{API_BASE}/auth/login"
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        print(f"🔐 Logging in as: {TEST_EMAIL}")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
            print(f"✅ Login successful!")
            print(f"   User ID: {self.user_id}")
            print(f"   Token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_jobs(self):
        """Test job listing"""
        self.print_section("2. Testing Job Browsing")
        
        url = f"{API_BASE}/jobs"
        print(f"📋 Fetching jobs from: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Retrieved {len(jobs)} jobs")
            
            if len(jobs) > 0:
                self.job_ids = [job.get('id') for job in jobs[:5]]
                print(f"\n   Sample jobs:")
                for i, job in enumerate(jobs[:3], 1):
                    print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company_name', 'N/A')}")
                    print(f"      Location: {job.get('location', 'N/A')}")
                    print(f"      Type: {job.get('job_type', 'N/A')}")
            else:
                print("⚠️  No jobs found in database")
                print("   You may need to seed jobs first")
            return True
        else:
            print(f"❌ Failed to fetch jobs: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_seed_jobs(self):
        """Seed sample jobs if none exist"""
        self.print_section("2a. Seeding Sample Jobs")
        
        url = f"{API_BASE}/jobs/seed"
        print(f"🌱 Seeding jobs...")
        
        response = requests.post(url, headers=self.get_headers())
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Jobs seeded successfully!")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Jobs created: {data.get('jobs_created', 0)}")
            return True
        else:
            print(f"❌ Failed to seed jobs: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_search_jobs(self):
        """Test job search functionality"""
        self.print_section("3. Testing Job Search")
        
        search_query = "python developer"
        url = f"{API_BASE}/jobs/search?q={search_query}"
        print(f"🔍 Searching for: '{search_query}'")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} matching jobs")
            
            if len(results) > 0:
                print(f"\n   Top results:")
                for i, job in enumerate(results[:3], 1):
                    print(f"   {i}. {job.get('title', 'N/A')} at {job.get('company_name', 'N/A')}")
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    
    def test_resume_upload(self):
        """Test resume upload (simulated)"""
        self.print_section("4. Testing Resume Upload")
        
        print("📄 Testing resume upload functionality...")
        
        # Create a sample resume text
        sample_resume_text = """
        John Doe
        Software Engineer
        
        SKILLS:
        - Python, JavaScript, React, Node.js
        - Machine Learning, TensorFlow, PyTorch
        - SQL, PostgreSQL, MongoDB
        - AWS, Docker, Kubernetes
        
        EXPERIENCE:
        Senior Software Engineer at Tech Corp (2020-Present)
        - Developed scalable web applications
        - Led team of 5 engineers
        - Implemented CI/CD pipelines
        
        EDUCATION:
        BS Computer Science, University of Technology (2016-2020)
        """
        
        url = f"{API_BASE}/resumes/upload"
        
        # Simulate file upload with multipart/form-data
        files = {
            'file': ('resume.txt', sample_resume_text.encode(), 'text/plain')
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"📤 Uploading resume...")
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.resume_id = data.get('id')
            print(f"✅ Resume uploaded successfully!")
            print(f"   Resume ID: {self.resume_id}")
            print(f"   Skills extracted: {data.get('skills', 'N/A')}")
            return True
        else:
            print(f"❌ Resume upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_get_resumes(self):
        """Test resume listing"""
        self.print_section("5. Testing Resume Retrieval")
        
        url = f"{API_BASE}/resumes"
        print(f"📋 Fetching user resumes...")
        
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            resumes = response.json()
            print(f"✅ Retrieved {len(resumes)} resume(s)")
            
            if len(resumes) > 0:
                for i, resume in enumerate(resumes, 1):
                    print(f"\n   Resume {i}:")
                    print(f"   - ID: {resume.get('id')}")
                    print(f"   - Filename: {resume.get('file_name', 'N/A')}")
                    print(f"   - Skills: {resume.get('skills', 'N/A')[:100]}...")
                    if not self.resume_id:
                        self.resume_id = resume.get('id')
            return True
        else:
            print(f"❌ Failed to fetch resumes: {response.status_code}")
            return False
    
    def test_job_recommendations(self):
        """Test AI-powered job recommendations"""
        self.print_section("6. Testing Job Recommendations")
        
        if not self.resume_id:
            print("⚠️  No resume ID available. Skipping recommendations test.")
            return False
        
        url = f"{API_BASE}/recommendations/jobs-for-resume/{self.resume_id}"
        print(f"🤖 Getting AI recommendations for resume: {self.resume_id}")
        
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"✅ Received {len(recommendations)} job recommendations")
            
            if len(recommendations) > 0:
                print(f"\n   Top recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    job = rec.get('job', {})
                    score = rec.get('similarity_score', 0)
                    print(f"\n   {i}. {job.get('title', 'N/A')} at {job.get('company_name', 'N/A')}")
                    print(f"      Match Score: {score:.2%}")
                    print(f"      Location: {job.get('location', 'N/A')}")
            else:
                print("⚠️  No recommendations generated")
                print("   This may be because:")
                print("   - No jobs have embeddings yet")
                print("   - Resume doesn't have embeddings")
                print("   - No matching jobs found")
            return True
        else:
            print(f"❌ Recommendations failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_resume_quality(self):
        """Test resume quality analysis"""
        self.print_section("7. Testing Resume Quality Analysis")
        
        if not self.resume_id:
            print("⚠️  No resume ID available. Skipping quality analysis.")
            return False
        
        url = f"{API_BASE}/recommendations/resume-quality/{self.resume_id}"
        print(f"📊 Analyzing resume quality...")
        
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            quality = response.json()
            print(f"✅ Resume quality analysis complete!")
            print(f"\n   Overall Score: {quality.get('overall_score', 'N/A')}")
            print(f"   Completeness: {quality.get('completeness', 'N/A')}")
            print(f"   Suggestions:")
            for suggestion in quality.get('suggestions', []):
                print(f"   - {suggestion}")
            return True
        else:
            print(f"❌ Quality analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def test_applications(self):
        """Test application tracking"""
        self.print_section("8. Testing Application Tracking")
        
        if not self.job_ids:
            print("⚠️  No job IDs available. Skipping application test.")
            return False
        
        # Create an application
        url = f"{API_BASE}/applications"
        payload = {
            "job_id": self.job_ids[0],
            "resume_id": self.resume_id,
            "status": "applied",
            "notes": "Test application created via API"
        }
        
        print(f"📝 Creating test application...")
        response = requests.post(url, json=payload, headers=self.get_headers())
        
        if response.status_code in [200, 201]:
            app = response.json()
            print(f"✅ Application created successfully!")
            print(f"   Application ID: {app.get('id')}")
            print(f"   Status: {app.get('status')}")
            
            # List applications
            print(f"\n📋 Fetching all applications...")
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                apps = response.json()
                print(f"✅ Retrieved {len(apps)} application(s)")
                return True
        else:
            print(f"❌ Application creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all feature tests"""
        print("\n" + "="*60)
        print("  🚀 AutoIntern Feature Testing Suite")
        print("="*60)
        
        results = {}
        
        # Test 1: Authentication
        results['login'] = self.test_login()
        if not results['login']:
            print("\n❌ Cannot proceed without authentication")
            return results
        
        # Test 2: Job Browsing
        results['get_jobs'] = self.test_get_jobs()
        
        # Test 2a: Seed jobs if none exist
        if results['get_jobs'] and len(self.job_ids) == 0:
            results['seed_jobs'] = self.test_seed_jobs()
            # Retry getting jobs
            self.test_get_jobs()
        
        # Test 3: Job Search
        results['search_jobs'] = self.test_search_jobs()
        
        # Test 4: Resume Upload
        results['resume_upload'] = self.test_resume_upload()
        
        # Test 5: Resume Retrieval
        results['get_resumes'] = self.test_get_resumes()
        
        # Test 6: Job Recommendations
        results['recommendations'] = self.test_job_recommendations()
        
        # Test 7: Resume Quality
        results['resume_quality'] = self.test_resume_quality()
        
        # Test 8: Applications
        results['applications'] = self.test_applications()
        
        # Summary
        self.print_section("Test Summary")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"\nDetailed Results:")
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test}")
        
        print(f"\n{'='*60}\n")
        
        return results


if __name__ == "__main__":
    tester = AutoInternTester()
    tester.run_all_tests()
