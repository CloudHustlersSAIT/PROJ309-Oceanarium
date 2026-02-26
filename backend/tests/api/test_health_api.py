"""API endpoint tests for Health."""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _mock_engine():
    mock_conn = MagicMock()
    results = iter([
        "PostgreSQL 16.1",
        "100",
        5,
    ])
    mock_conn.execute.return_value.scalar.side_effect = lambda: next(results)
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_eng = MagicMock()
    mock_eng.connect.return_value = mock_ctx
    return mock_eng


def test_health(client):
    with patch("app.routers.health.engine", _mock_engine()):
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_version"] == "PostgreSQL 16.1"
    assert data["max_connections"] == 100
    assert data["active_connections"] == 5


def test_health_db_failure(client):
    with patch("app.routers.health.engine") as mock_eng:
        mock_eng.connect.side_effect = Exception("DB down")
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert "DB down" in data["detail"]
