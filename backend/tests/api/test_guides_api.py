"""API endpoint tests for Guides."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _guide_payload(**overrides):
    defaults = {
        "first_name": "Ana",
        "last_name": "Costa",
        "email": "ana@test.com",
        "phone": "+351999",
        "languages": ["en"],
        "expertises": [{"name": "Sharks", "category": "Marine Biology"}],
    }
    defaults.update(overrides)
    return defaults


def test_list_guides_empty(client, db):
    resp = client.get("/guides")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_guide(client, db):
    resp = client.post("/guides", json=_guide_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Ana"
    assert data["last_name"] == "Costa"
    assert data["phone"] == "+351999"
    assert len(data["languages"]) == 1


def test_get_guide(client, db):
    create = client.post("/guides", json=_guide_payload())
    guide_id = create.json()["id"]
    resp = client.get(f"/guides/{guide_id}")
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Ana"


def test_get_guide_not_found(client, db):
    resp = client.get("/guides/9999")
    assert resp.status_code == 404


def test_update_guide(client, db):
    create = client.post("/guides", json=_guide_payload())
    guide_id = create.json()["id"]
    resp = client.patch(f"/guides/{guide_id}", json={"first_name": "Maria"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Maria"


def test_update_guide_not_found(client, db):
    resp = client.patch("/guides/9999", json={"first_name": "Maria"})
    assert resp.status_code == 404
