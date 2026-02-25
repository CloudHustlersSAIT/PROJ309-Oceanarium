"""API endpoint tests for Health."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_db(client):
    resp = client.get("/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_check"] == 1


def test_health_db_failure(client):
    from unittest.mock import patch

    with patch("app.routers.health.test_connection", side_effect=Exception("DB down")):
        resp = client.get("/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert "DB down" in data["detail"]
