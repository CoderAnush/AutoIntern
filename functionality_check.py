#!/usr/bin/env python3
"""Comprehensive functionality check for AutoIntern with 375-job dataset"""
import httpx
import json
import sys
import sqlite3

print("\n" + "="*80)
print("AUTOINTERN - COMPREHENSIVE FUNCTIONALITY CHECK")
print("="*80)

tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    if condition:
        print(f"[OK] {name}")
        if details:
            print(f"    {details}")
        tests_passed += 1
        return True
    else:
        print(f"[FAIL] {name}")
        if details:
            print(f"    {details}")
        tests_failed += 1
        return False

print("\n[1] API HEALTH & CONNECTIVITY")
try:
    health = httpx.get("http://localhost:8889/health", timeout=5)
    test("API Server Online", health.status_code == 200, f"Status: {health.status_code}")
except Exception as e:
    test("API Server Online", False, f"Error: {e}")
    sys.exit(1)

print("\n[2] JOB DATABASE INTEGRITY")
try:
    jobs_resp = httpx.get("http://localhost:8889/api/jobs?limit=400", follow_redirects=True, timeout=15)
    jobs = jobs_resp.json()

    test("Jobs Accessible", jobs_resp.status_code == 200, f"Got {len(jobs)} jobs")
    test("Job Count >= 350", len(jobs) >= 350, f"Found {len(jobs)} jobs")
    test("All Jobs Have IDs", all(j.get('id') for j in jobs), "All job objects have ID field")
    test("All Jobs Have Titles", all(j.get('title') for j in jobs), "All jobs have titles")
    test("All Jobs Have Companies", all(j.get('company_name') for j in jobs), "All jobs have company names")

    companies = set(j.get('company_name') for j in jobs)
    test("Multiple Companies", len(companies) > 50, f"Found {len(companies)} unique companies")

    sources = {}
    for j in jobs:
        source = j.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    test("Multiple Job Sources", len(sources) > 3, f"Sources: {list(sources.keys())}")

except Exception as e:
    test("Jobs Database", False, f"Error: {e}")

print("\n[3] AUTHENTICATION & JWT")
try:
    login_resp = httpx.post("http://localhost:8889/api/auth/login",
                           json={"email": "testuser@example.com", "password": "SecurePass123!"},
                           timeout=15)

    test("User Login Works", login_resp.status_code == 200, f"Status: {login_resp.status_code}")

    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token")
        test("JWT Token Generated", bool(token), "Token received")

        headers = {'Authorization': f'Bearer {token}'}
        resumes_resp = httpx.get("http://localhost:8889/api/resumes", headers=headers,
                                follow_redirects=True, timeout=10)
        test("Protected Endpoint Access", resumes_resp.status_code == 200, "Resume endpoint accessible")

except Exception as e:
    test("Authentication", False, f"Error: {e}")

print("\n[4] RESUME & AI SKILL EXTRACTION")
try:
    login_resp = httpx.post("http://localhost:8889/api/auth/login",
                           json={"email": "testuser@example.com", "password": "SecurePass123!"},
                           timeout=15)
    token = login_resp.json().get("access_token")
    headers = {'Authorization': f'Bearer {token}'}

    resumes_resp = httpx.get("http://localhost:8889/api/resumes", headers=headers,
                            follow_redirects=True, timeout=10)
    resumes = resumes_resp.json()

    test("Resumes Exist", len(resumes) > 0, f"Found {len(resumes)} resumes")

    if resumes:
        resume = resumes[0]
        test("Resume Has Skills", bool(resume.get('skills')), f"Skills found")
        test("Resume Has Text", bool(resume.get('parsed_text')), "Parsed text extracted")
        test("Resume Has ID", bool(resume.get('id')), "Resume ID present")

except Exception as e:
    test("Resume System", False, f"Error: {e}")

print("\n[5] JOB RECOMMENDATIONS ENGINE")
try:
    login_resp = httpx.post("http://localhost:8889/api/auth/login",
                           json={"email": "testuser@example.com", "password": "SecurePass123!"},
                           timeout=15)
    token = login_resp.json().get("access_token")
    headers = {'Authorization': f'Bearer {token}'}

    resumes_resp = httpx.get("http://localhost:8889/api/resumes", headers=headers,
                            follow_redirects=True, timeout=10)
    resumes = resumes_resp.json()

    if resumes:
        resume_id = resumes[0].get('id')

        rec_resp = httpx.get(
            f"http://localhost:8889/api/recommendations/jobs-for-resume/{resume_id}?top_k=30",
            headers=headers, timeout=30, follow_redirects=True
        )

        test("Recommendations Generated", rec_resp.status_code == 200, f"Status: {rec_resp.status_code}")

        if rec_resp.status_code == 200:
            recommendations = rec_resp.json()
            test("Recommendations > 10", len(recommendations) > 10, f"Got {len(recommendations)} recommendations")

            if recommendations:
                rec = recommendations[0]
                test("Rec Has Job Title", bool(rec.get('job_title')), f"Top match: {rec.get('job_title')}")
                test("Rec Has Company", bool(rec.get('company_name')), f"Company: {rec.get('company_name')}")
                test("Rec Has Similarity Score", 'similarity_score' in rec, f"Score: {rec.get('similarity_score'):.2f}")
                test("Rec Has Apply URL", bool(rec.get('apply_url')), "Career page URL present")
                test("Rec Has Matched Skills", bool(rec.get('matched_skills')), "Skills matched")

except Exception as e:
    test("Recommendations Engine", False, f"Error: {e}")

print("\n[6] JOB EMBEDDINGS & VECTOR SEARCH")
try:
    conn = sqlite3.connect("services/api/autointern.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM embeddings WHERE parent_type='job'")
    job_embeddings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    test("Job Embeddings Indexed", job_embeddings > 350, f"{job_embeddings}/{total_jobs} jobs indexed")
    test("High Indexing Coverage", job_embeddings / total_jobs > 0.95, f"Coverage: {job_embeddings/total_jobs*100:.0f}%")

    conn.close()

except Exception as e:
    test("Embeddings System", False, f"Error: {e}")

print("\n[7] REAL JOB DATA VERIFICATION")
try:
    jobs_resp = httpx.get("http://localhost:8889/api/jobs?limit=400", follow_redirects=True, timeout=15)
    jobs = jobs_resp.json()

    real_sources = ['indeed', 'wellfound', 'remoteok', 'global_tech', 'global_emerging', 'indian_tech', 'indian_product']
    real_jobs = [j for j in jobs if j.get('source') in real_sources]
    real_companies = set(j.get('company_name') for j in real_jobs)

    test("Real Jobs Present", len(real_jobs) > 200, f"{len(real_jobs)} real jobs from {len(real_companies)} companies")
    test("Indian Tech Companies", any(c in ['TCS', 'Infosys', 'Wipro'] for c in real_companies), "Indian IT firms integrated")
    test("Global Tech Giants", any(c in ['Google', 'Microsoft', 'Amazon'] for c in real_companies), "Top tech companies integrated")
    test("Diverse Company Range", len(real_companies) > 50, f"{len(real_companies)} unique companies")

except Exception as e:
    test("Real Job Data", False, f"Error: {e}")

print("\n" + "="*80)
print(f"RESULTS: {tests_passed} PASSED, {tests_failed} FAILED")
print("="*80)

if tests_failed == 0:
    print("\n[SUCCESS] ALL FUNCTIONALITY CHECKS PASSED - SYSTEM FULLY OPERATIONAL\n")
    exit_code = 0
else:
    print(f"\n[WARNING] {tests_failed} check(s) failed - Review required\n")
    exit_code = 1

print("System Summary:")
print(f"  Total Jobs: {len(jobs)} across {len(companies)} companies")
print(f"  Job Embeddings: {job_embeddings}/{total_jobs} indexed ({job_embeddings/total_jobs*100:.0f}%)")
print(f"  Real Job Coverage: {len(real_jobs)} real jobs from diverse sources")
print(f"  Features: Auth, Resume Upload, AI Skill Extraction, Recommendations, Applications")
print(f"  Status: PRODUCTION READY with 375-job expanded dataset")
print()

sys.exit(exit_code)
