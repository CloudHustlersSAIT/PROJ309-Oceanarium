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
