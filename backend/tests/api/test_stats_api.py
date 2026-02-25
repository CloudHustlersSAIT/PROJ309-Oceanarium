"""API endpoint tests for Stats."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_read_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "toursToday" in data
    assert "customersToday" in data
    assert "cancellations" in data
    assert "avgRating" in data


def test_stats_returns_expected_mock_values(client):
    resp = client.get("/stats")
    data = resp.json()
    assert data["toursToday"] == 14
    assert data["customersToday"] == 45
    assert data["cancellations"] == 2
    assert data["avgRating"] == "4.9"
