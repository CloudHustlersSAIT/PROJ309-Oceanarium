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


def test_update_guide_all_fields(client, db):
    create = client.post("/guides", json=_guide_payload())
    guide_id = create.json()["id"]
    resp = client.patch(f"/guides/{guide_id}", json={
        "first_name": "Maria",
        "last_name": "Silva",
        "email": "maria@test.com",
        "phone": "+351111",
        "guide_rating": 4.5,
        "is_active": False,
        "languages": ["pt"],
        "tour_type_ids": [],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["last_name"] == "Silva"
    assert data["email"] == "maria@test.com"
    assert data["phone"] == "+351111"
    assert data["guide_rating"] == 4.5
    assert data["is_active"] is False
    assert data["languages"][0]["code"] == "pt"


def test_update_guide_not_found(client, db):
    resp = client.patch("/guides/9999", json={"first_name": "Maria"})
    assert resp.status_code == 404


def test_set_availability(client, db):
    create = client.post("/guides", json=_guide_payload())
    guide_id = create.json()["id"]
    resp = client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "America/Toronto",
        "slots": [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
        ],
        "exceptions": [
            {"date": "2026-04-01", "type": "blocked", "reason": "Holiday"},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    ap = data["availability_pattern"]
    assert ap["timezone"] == "America/Toronto"
    assert len(ap["slots"]) == 1
    assert len(ap["exceptions"]) == 1


def test_set_availability_replaces_existing(client, db):
    create = client.post("/guides", json=_guide_payload())
    guide_id = create.json()["id"]
    client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "UTC",
        "slots": [{"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"}],
        "exceptions": [],
    })
    resp = client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "Europe/Lisbon",
        "slots": [{"day_of_week": 2, "start_time": "10:00", "end_time": "18:00"}],
        "exceptions": [],
    })
    assert resp.status_code == 200
    assert resp.json()["availability_pattern"]["timezone"] == "Europe/Lisbon"


def test_set_availability_not_found(client, db):
    resp = client.put("/guides/9999/availability", json={
        "timezone": "UTC",
        "slots": [],
        "exceptions": [],
    })
    assert resp.status_code == 404


def test_update_guide_with_tour_types(client, db):
    tour_resp = client.post("/tours", json={"name": "Reef Tour", "duration": 90})
    tour_id = tour_resp.json()["id"]
    create = client.post("/guides", json=_guide_payload(tour_type_ids=[tour_id]))
    guide_id = create.json()["id"]
    data = create.json()
    assert len(data["tour_types"]) == 1
    assert data["tour_types"][0]["id"] == tour_id

    resp = client.patch(f"/guides/{guide_id}", json={"tour_type_ids": []})
    assert resp.status_code == 200
    assert resp.json()["tour_types"] == []
