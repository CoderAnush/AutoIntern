import requests
import sqlite3
import json

DATABASE_URL = "services/api/autointern.db"

def check_db_direct():
    print("📊 Checking Database Directly...")
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check users
        cursor.execute("SELECT count(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Users: {user_count}")
        
        # Check jobs
        cursor.execute("SELECT count(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        print(f"  Jobs: {job_count}")
        
        # Check resumes
        cursor.execute("SELECT count(*) FROM resumes")
        resume_count = cursor.fetchone()[0]
        print(f"  Resumes: {resume_count}")
        
        # Check embeddings
        cursor.execute("SELECT count(*) FROM embeddings")
        embedding_count = cursor.fetchone()[0]
        print(f"  Embeddings: {embedding_count}")
        
        conn.close()
        return embedding_count > 0
    except Exception as e:
        print(f"❌ DB Check Failed: {e}")
        return False

def check_api_auth():
    print("\n🔐 Checking API Authentication...")
    try:
        # Login
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        resp = requests.post("http://localhost:8000/api/auth/login", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Login Failed: {resp.status_code} - {resp.text}")
            return False
            
        token = resp.json()["access_token"]
        print(f"✅ Login Successful. Token: {token[:20]}...")
        
        # Check /users/me
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get("http://localhost:8000/api/auth/me", headers=headers)
        if resp.status_code == 200:
            print(f"✅ /api/auth/me Successful: {resp.json().get('email')}")
            return True
        else:
            print(f"❌ /api/auth/me Failed: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Check Failed: {e}")
        return False

if __name__ == "__main__":
    embeddings_exist = check_db_direct()
    auth_works = check_api_auth()
    
    if embeddings_exist and auth_works:
        print("\n🎉 SUCCESS: Embeddings exist and Auth works!")
    else:
        print("\n⚠️ ISSUES FOUND")
