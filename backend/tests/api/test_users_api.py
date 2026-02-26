"""API endpoint tests for Users."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_list_users_empty(client, db):
    resp = client.get("/users")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_user(client, db):
    resp = client.post("/users", json={
        "username": "admin",
        "email": "admin@test.com",
        "password_hash": "hashed_pw",
        "full_name": "Admin User",
        "role": "admin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_get_user(client, db):
    create = client.post("/users", json={
        "username": "testuser",
        "email": "test@test.com",
        "password_hash": "hash",
        "full_name": "Test User",
        "role": "user",
    })
    user_id = create.json()["id"]
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_get_user_not_found(client, db):
    resp = client.get("/users/9999")
    assert resp.status_code == 404


def test_update_user(client, db):
    create = client.post("/users", json={
        "username": "olduser",
        "email": "old@test.com",
        "password_hash": "hash",
        "full_name": "Old Name",
        "role": "user",
    })
    user_id = create.json()["id"]
    resp = client.patch(f"/users/{user_id}", json={"full_name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"


def test_update_user_all_fields(client, db):
    create = client.post("/users", json={
        "username": "original",
        "email": "orig@test.com",
        "password_hash": "hash",
        "full_name": "Original",
        "role": "user",
    })
    user_id = create.json()["id"]
    resp = client.patch(f"/users/{user_id}", json={
        "username": "updated",
        "email": "new@test.com",
        "full_name": "Updated Name",
        "role": "admin",
        "is_active": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "updated"
    assert data["email"] == "new@test.com"
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "admin"
    assert data["is_active"] is False


def test_update_user_not_found(client, db):
    resp = client.patch("/users/9999", json={"full_name": "X"})
    assert resp.status_code == 404


def test_delete_user(client, db):
    create = client.post("/users", json={
        "username": "temp",
        "email": "temp@test.com",
        "password_hash": "hash",
        "full_name": "Temp",
        "role": "user",
    })
    user_id = create.json()["id"]
    resp = client.delete(f"/users/{user_id}")
    assert resp.status_code == 204


def test_delete_user_not_found(client, db):
    resp = client.delete("/users/9999")
    assert resp.status_code == 404
