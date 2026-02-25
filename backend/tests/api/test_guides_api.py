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


def test_get_guide_detail(client):
    create_resp = client.post("/guides", json={
        "name": "Detail Guide", "email": "detail@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.get(f"/guides/{guide_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Detail Guide"
    assert data["email"] == "detail@test.com"
    assert len(data["languages"]) == 1
    assert data["availability_pattern"] is None


def test_update_guide(client):
    create_resp = client.post("/guides", json={
        "name": "Original", "email": "update@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.patch(f"/guides/{guide_id}", json={
        "name": "Updated Name",
        "is_active": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False


def test_update_guide_languages(client):
    create_resp = client.post("/guides", json={
        "name": "Lang Guide", "email": "lang@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.patch(f"/guides/{guide_id}", json={
        "languages": ["pt", "fr"],
    })
    assert resp.status_code == 200
    codes = {l["code"] for l in resp.json()["languages"]}
    assert codes == {"pt", "fr"}


def test_update_guide_expertises(client):
    create_resp = client.post("/guides", json={
        "name": "Exp Guide", "email": "exp@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.patch(f"/guides/{guide_id}", json={
        "expertises": ["Dolphins", "Coral Reef"],
    })
    assert resp.status_code == 200
    names = {e["name"] for e in resp.json()["expertises"]}
    assert names == {"Dolphins", "Coral Reef"}


def test_update_guide_email(client):
    create_resp = client.post("/guides", json={
        "name": "Email Guide", "email": "oldemail@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    resp = client.patch(f"/guides/{guide_id}", json={"email": "newemail@test.com"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "newemail@test.com"


def test_update_guide_not_found(client):
    resp = client.patch("/guides/9999", json={"name": "Ghost"})
    assert resp.status_code == 404


def test_set_availability_not_found(client):
    resp = client.put("/guides/9999/availability", json={
        "timezone": "UTC",
        "slots": [],
        "exceptions": [],
    })
    assert resp.status_code == 404


def test_set_availability_replaces_existing(client):
    create_resp = client.post("/guides", json={
        "name": "Avail Replace", "email": "replace@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    guide_id = create_resp.json()["id"]

    client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "UTC",
        "slots": [{"day_of_week": 0, "start_time": "08:00", "end_time": "17:00"}],
        "exceptions": [],
    })

    resp = client.put(f"/guides/{guide_id}/availability", json={
        "timezone": "Europe/Lisbon",
        "slots": [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "16:00"},
            {"day_of_week": 2, "start_time": "10:00", "end_time": "15:00"},
        ],
        "exceptions": [{"date": "2026-04-01", "type": "blocked", "reason": "Vacation"}],
    })
    assert resp.status_code == 200
    pattern = resp.json()["availability_pattern"]
    assert pattern["timezone"] == "Europe/Lisbon"
    assert len(pattern["slots"]) == 2
    assert len(pattern["exceptions"]) == 1


def test_create_guide_default_is_active(client):
    resp = client.post("/guides", json={
        "name": "Default Active", "email": "default@test.com",
        "languages": ["en"], "expertises": ["Sharks"],
    })
    assert resp.status_code == 201
    assert resp.json()["is_active"] is True
