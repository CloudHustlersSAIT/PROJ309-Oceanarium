"""API endpoint tests for Sync (Phase 7d)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.adapters.clorian_mock import ClorianMockClient
from app.jobs.sync_scheduler import init_sync_service


def test_trigger_sync(client, db):
    init_sync_service(ClorianMockClient())

    resp = client.post("/sync/trigger")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "new_count" in data


def test_get_sync_logs(client, db):
    init_sync_service(ClorianMockClient())
    client.post("/sync/trigger")

    resp = client.get("/sync/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["status"] == "success"


def test_get_sync_logs_empty(client, db):
    resp = client.get("/sync/logs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_sync_logs_with_limit_and_offset(client, db):
    init_sync_service(ClorianMockClient())
    client.post("/sync/trigger")
    client.post("/sync/trigger")

    resp = client.get("/sync/logs?limit=1&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp2 = client.get("/sync/logs?limit=1&offset=1")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


def test_trigger_sync_without_service(client, db):
    from app.jobs import sync_scheduler

    original = sync_scheduler._sync_service
    sync_scheduler._sync_service = None
    try:
        resp = client.post("/sync/trigger")
        assert resp.status_code == 503
    finally:
        sync_scheduler._sync_service = original
