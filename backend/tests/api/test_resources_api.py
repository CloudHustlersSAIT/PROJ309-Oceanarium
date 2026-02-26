"""API endpoint tests for Resources."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_list_resources_empty(client, db):
    resp = client.get("/resources")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_resource(client, db):
    resp = client.post("/resources", json={
        "name": "Boat",
        "type": "vehicle",
        "quantity_available": 5,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Boat"
    assert data["quantity_available"] == 5


def test_get_resource(client, db):
    create = client.post("/resources", json={
        "name": "Wetsuit",
        "type": "equipment",
        "quantity_available": 20,
    })
    resource_id = create.json()["id"]
    resp = client.get(f"/resources/{resource_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Wetsuit"


def test_get_resource_not_found(client, db):
    resp = client.get("/resources/9999")
    assert resp.status_code == 404


def test_update_resource(client, db):
    create = client.post("/resources", json={"name": "Old Name"})
    resource_id = create.json()["id"]
    resp = client.patch(f"/resources/{resource_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_resource(client, db):
    create = client.post("/resources", json={"name": "Disposable"})
    resource_id = create.json()["id"]
    resp = client.delete(f"/resources/{resource_id}")
    assert resp.status_code == 204
