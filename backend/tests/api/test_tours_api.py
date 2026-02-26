"""API endpoint tests for Tours."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_list_tours_empty(client, db):
    resp = client.get("/tours")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_tour(client, db):
    resp = client.post("/tours", json={
        "name": "Shark Diving",
        "description": "Exciting!",
        "duration": 120,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Shark Diving"
    assert data["duration"] == 120


def test_get_tour(client, db):
    create = client.post("/tours", json={"name": "Dolphin Watch", "duration": 60})
    tour_id = create.json()["id"]
    resp = client.get(f"/tours/{tour_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Dolphin Watch"


def test_get_tour_not_found(client, db):
    resp = client.get("/tours/9999")
    assert resp.status_code == 404


def test_update_tour(client, db):
    create = client.post("/tours", json={"name": "Old Name"})
    tour_id = create.json()["id"]
    resp = client.patch(f"/tours/{tour_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_tour(client, db):
    create = client.post("/tours", json={"name": "To Delete"})
    tour_id = create.json()["id"]
    resp = client.delete(f"/tours/{tour_id}")
    assert resp.status_code == 204

    get_resp = client.get(f"/tours/{tour_id}")
    assert get_resp.status_code == 404
