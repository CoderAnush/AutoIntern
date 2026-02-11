import pytest
import time
import pytest
pytest.importorskip('fastapi')
from fastapi.testclient import TestClient
from app.main import app
import psycopg2

client = TestClient(app)


def is_db_available():
    try:
        conn = psycopg2.connect(dbname="autointern", user="autointern", password="change-me", host="localhost", port=5432)
        conn.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not is_db_available(), reason="Postgres not available")
def test_db_health():
    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json().get("db") == "ok"


@pytest.mark.skipif(not is_db_available(), reason="Postgres not available")
def test_create_and_list_job():
    payload = {"title": "Test Job", "description": "Testing", "location": "Remote"}
    post = client.post("/jobs", json=payload)
    assert post.status_code == 201
    data = post.json()
    assert data["title"] == "Test Job"

    get = client.get("/jobs")
    assert get.status_code == 200
    items = get.json()
    assert any(j["id"] == data["id"] for j in items)
