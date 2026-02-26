"""API endpoint tests for Surveys."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_booking, make_customer, make_guide


def test_list_surveys_empty(client, db):
    resp = client.get("/surveys")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_survey(client, db):
    customer = make_customer(db)
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    resp = client.post("/surveys", json={
        "customer_id": customer.id,
        "guide_id": guide.id,
        "booking_version_id": lv.id,
        "rating": 5,
        "comment": "Excellent!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5
    assert data["comment"] == "Excellent!"


def test_get_survey(client, db):
    customer = make_customer(db)
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/surveys", json={
        "customer_id": customer.id,
        "guide_id": guide.id,
        "booking_version_id": lv.id,
        "rating": 4,
    })
    survey_id = create.json()["id"]
    resp = client.get(f"/surveys/{survey_id}")
    assert resp.status_code == 200
    assert resp.json()["rating"] == 4


def test_get_survey_not_found(client, db):
    resp = client.get("/surveys/9999")
    assert resp.status_code == 404


def test_update_survey(client, db):
    customer = make_customer(db)
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/surveys", json={
        "customer_id": customer.id,
        "guide_id": guide.id,
        "booking_version_id": lv.id,
        "rating": 3,
        "comment": "OK",
    })
    survey_id = create.json()["id"]
    resp = client.patch(f"/surveys/{survey_id}", json={
        "rating": 5,
        "comment": "Actually great!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["rating"] == 5
    assert data["comment"] == "Actually great!"


def test_update_survey_not_found(client, db):
    resp = client.patch("/surveys/9999", json={"rating": 1})
    assert resp.status_code == 404


def test_delete_survey(client, db):
    customer = make_customer(db)
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/surveys", json={
        "customer_id": customer.id,
        "guide_id": guide.id,
        "booking_version_id": lv.id,
        "rating": 3,
    })
    survey_id = create.json()["id"]
    resp = client.delete(f"/surveys/{survey_id}")
    assert resp.status_code == 204


def test_delete_survey_not_found(client, db):
    resp = client.delete("/surveys/9999")
    assert resp.status_code == 404
