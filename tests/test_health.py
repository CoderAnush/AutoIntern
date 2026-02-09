import pytest
pytest.importorskip('fastapi')
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
