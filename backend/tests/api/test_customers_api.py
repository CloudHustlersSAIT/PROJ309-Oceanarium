"""API endpoint tests for Customers."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_list_customers_empty(client, db):
    resp = client.get("/customers")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_customer(client, db):
    resp = client.post("/customers", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "John"
    assert data["phone"] == "+1234567890"


def test_get_customer(client, db):
    create = client.post("/customers", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@test.com",
    })
    customer_id = create.json()["id"]
    resp = client.get(f"/customers/{customer_id}")
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Jane"


def test_get_customer_not_found(client, db):
    resp = client.get("/customers/9999")
    assert resp.status_code == 404


def test_update_customer(client, db):
    create = client.post("/customers", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
    })
    customer_id = create.json()["id"]
    resp = client.patch(f"/customers/{customer_id}", json={"first_name": "Jonathan"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Jonathan"


def test_update_customer_all_fields(client, db):
    create = client.post("/customers", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
        "phone": "+1111",
    })
    customer_id = create.json()["id"]
    resp = client.patch(f"/customers/{customer_id}", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@test.com",
        "phone": "+2222",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert data["email"] == "jane@test.com"
    assert data["phone"] == "+2222"


def test_update_customer_not_found(client, db):
    resp = client.patch("/customers/9999", json={"first_name": "X"})
    assert resp.status_code == 404


def test_delete_customer(client, db):
    create = client.post("/customers", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
    })
    customer_id = create.json()["id"]
    resp = client.delete(f"/customers/{customer_id}")
    assert resp.status_code == 204


def test_delete_customer_not_found(client, db):
    resp = client.delete("/customers/9999")
    assert resp.status_code == 404
