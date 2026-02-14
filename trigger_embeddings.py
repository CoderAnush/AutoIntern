import requests
import time

def trigger_embeddings():
    print("🚀 Triggering embeddings generation...")
    try:
        response = requests.post("http://localhost:8000/api/admin/generate-embeddings")
        print(f"Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Failed to trigger embeddings: {e}")

if __name__ == "__main__":
    # Wait a bit for server to reload if needed
    time.sleep(2)
    trigger_embeddings()
