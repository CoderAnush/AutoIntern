import os
import pytest
pytest.importorskip('aioredis')
from fastapi.testclient import TestClient
from services.api.app.main import app
from app.core.config import settings

client = TestClient(app)
REDIS_URL = f"redis://{settings.redis_host}:{settings.redis_port}"

@pytest.mark.skipif(not os.getenv('ADMIN_API_KEY'), reason='ADMIN_API_KEY not set')
def test_list_and_requeue_delete(monkeypatch):
    # Ensure Redis available
    import aioredis
    try:
        r = aioredis.from_url(REDIS_URL)
    except Exception:
        pytest.skip('Redis not available')

    # Ensure admin key is set in settings for the test
    monkeypatch.setattr(settings, 'admin_api_key', os.getenv('ADMIN_API_KEY'))

    # push a test DLQ item
    payload = {'job': {'source': 'test', 'external_id': 'dlq-1', 'title': 'DLQ Job'}}
    r.lpush('ingest:dlq', '{}'.format(payload))

    headers = {'X-Admin-Token': os.getenv('ADMIN_API_KEY')}

    res = client.get('/admin/dlq', headers=headers)
    assert res.status_code == 200
    items = res.json().get('items', [])
    assert len(items) >= 1

    # Requeue first item
    res = client.post('/admin/dlq/requeue', json={'index': 0}, headers=headers)
    assert res.status_code == 200
    assert res.json().get('status') == 'requeued'

    # Delete any leftover DLQ item (if any)
    res = client.delete('/admin/dlq', params={'index': 0}, headers=headers)
    # success or 404 acceptable
    assert res.status_code in (200, 404)

    # clean up redis
    r.close()
