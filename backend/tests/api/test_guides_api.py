"""API endpoint tests for Guides (Phase 7d)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_create_guide(client):
    resp = client.post("/guides", json={
        "name": "Ana Costa",
        "email": "ana@oceanarium.com",
        "is_active": True,
        "languages": ["en", "pt"],
        "expertises": ["Sharks"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ana Costa"
    assert len(data["languages"]) == 2
    assert len(data["expertises"]) == 1


def test_list_guides(client):
    client.post("/guides", json={
        "name": "Guide 1", "email": "g1@test.com", "languages": ["en"], "expertises": ["Sharks"],
    })
    client.post("/guides", json={
        "name": "Guide 2", "email": "g2@test.com", "languages": ["pt"], "expertises": ["Dolphins"],
    })

    resp = client.get("/guides")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_update_guide_availability(client):
    create_resp = client.post("/guides", json={
        "name": "Avail Guide", "email": "avail@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "Europe/Lisbon",
        "slots": [
            {"day_of_week": 0, "start_time": "08:00", "end_time": "17:00"},
            {"day_of_week": 1, "start_time": "09:00", "end_time": "16:00"},
        ],
        "exceptions": [
            {"date": "2026-03-15", "type": "blocked", "reason": "Holiday"},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    pattern = data["availability_pattern"]
    assert pattern["timezone"] == "Europe/Lisbon"
    assert len(pattern["slots"]) == 2
    assert len(pattern["exceptions"]) == 1


def test_get_guide_not_found(client):
    resp = client.get("/guides/9999")
    assert resp.status_code == 404
