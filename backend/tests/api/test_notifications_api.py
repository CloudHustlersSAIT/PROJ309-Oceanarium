"""API endpoint tests for Notifications."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_read_notifications(client):
    resp = client.get("/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_notification_structure(client):
    resp = client.get("/notifications")
    data = resp.json()
    for notification in data:
        assert "id" in notification
        assert "message" in notification
        assert "timestamp" in notification
