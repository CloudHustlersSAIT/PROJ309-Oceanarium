"""API endpoint tests for Issues."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_create_issue(client, db):
    resp = client.post("/issues", json={"description": "Broken handrail at tank 3"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Broken handrail at tank 3"
    assert "id" in data
    assert "created_at" in data


def test_create_issue_empty_description(client, db):
    resp = client.post("/issues", json={"description": ""})
    assert resp.status_code == 201
    assert resp.json()["description"] == ""


def test_create_issue_missing_description(client, db):
    resp = client.post("/issues", json={})
    assert resp.status_code == 422
