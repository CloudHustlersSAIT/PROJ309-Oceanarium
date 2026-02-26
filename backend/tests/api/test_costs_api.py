"""API endpoint tests for Costs."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _setup_tour(client):
    resp = client.post("/tours", json={"name": "Shark Dive", "duration": 120})
    return resp.json()["id"]


def test_list_costs_empty(client, db):
    resp = client.get("/costs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_cost(client, db):
    tour_id = _setup_tour(client)
    resp = client.post("/costs", json={
        "tour_id": tour_id,
        "ticket_type": "adult",
        "price": 50.00,
        "valid_from": "2026-01-01T00:00:00",
        "valid_to": "2026-12-31T23:59:59",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_type"] == "adult"
    assert data["price"] == 50.0


def test_get_cost(client, db):
    tour_id = _setup_tour(client)
    create = client.post("/costs", json={
        "tour_id": tour_id,
        "ticket_type": "child",
        "price": 25.00,
        "valid_from": "2026-01-01T00:00:00",
        "valid_to": "2026-12-31T23:59:59",
    })
    cost_id = create.json()["id"]
    resp = client.get(f"/costs/{cost_id}")
    assert resp.status_code == 200
    assert resp.json()["ticket_type"] == "child"


def test_get_cost_not_found(client, db):
    resp = client.get("/costs/9999")
    assert resp.status_code == 404


def test_update_cost(client, db):
    tour_id = _setup_tour(client)
    create = client.post("/costs", json={
        "tour_id": tour_id,
        "ticket_type": "adult",
        "price": 50.00,
        "valid_from": "2026-01-01T00:00:00",
        "valid_to": "2026-12-31T23:59:59",
    })
    cost_id = create.json()["id"]
    resp = client.patch(f"/costs/{cost_id}", json={"price": 60.00})
    assert resp.status_code == 200
    assert resp.json()["price"] == 60.0


def test_delete_cost(client, db):
    tour_id = _setup_tour(client)
    create = client.post("/costs", json={
        "tour_id": tour_id,
        "ticket_type": "adult",
        "price": 50.00,
        "valid_from": "2026-01-01T00:00:00",
        "valid_to": "2026-12-31T23:59:59",
    })
    cost_id = create.json()["id"]
    resp = client.delete(f"/costs/{cost_id}")
    assert resp.status_code == 204


def test_filter_costs_by_tour(client, db):
    tour_id = _setup_tour(client)
    client.post("/costs", json={
        "tour_id": tour_id,
        "ticket_type": "adult",
        "price": 50.00,
        "valid_from": "2026-01-01T00:00:00",
        "valid_to": "2026-12-31T23:59:59",
    })
    resp = client.get(f"/costs?tour_id={tour_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
