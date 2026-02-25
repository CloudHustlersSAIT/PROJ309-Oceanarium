"""API endpoint tests for Bookings."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_tour


def test_list_bookings_empty(client, db):
    resp = client.get("/bookings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_booking(client, db):
    tour = make_tour(db, clorian_booking_id="B-TOUR-1")
    db.commit()

    resp = client.post("/bookings", json={
        "customer_id": "CUST-001",
        "tour_id": tour.id,
        "date": "2026-03-02",
        "adult_tickets": 2,
        "child_tickets": 1,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_id"] == "CUST-001"
    assert data["tour_id"] == tour.id
    assert data["adult_tickets"] == 2
    assert data["child_tickets"] == 1
    assert data["status"] == "confirmed"


def test_list_bookings_after_create(client, db):
    tour = make_tour(db, clorian_booking_id="B-TOUR-2")
    db.commit()

    client.post("/bookings", json={
        "customer_id": "CUST-002",
        "tour_id": tour.id,
        "date": "2026-03-02",
        "adult_tickets": 1,
        "child_tickets": 0,
    })

    resp = client.get("/bookings")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["customer_id"] == "CUST-002"


def test_reschedule_booking(client, db):
    tour = make_tour(db, clorian_booking_id="B-TOUR-3")
    db.commit()

    create_resp = client.post("/bookings", json={
        "customer_id": "CUST-003",
        "tour_id": tour.id,
        "date": "2026-03-02",
        "adult_tickets": 2,
        "child_tickets": 0,
    })
    booking_id = create_resp.json()["booking_id"]

    resp = client.patch(f"/bookings/{booking_id}/reschedule", json={
        "new_date": "2026-03-10",
    })
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-03-10"


def test_reschedule_booking_not_found(client, db):
    resp = client.patch("/bookings/9999/reschedule", json={"new_date": "2026-03-10"})
    assert resp.status_code == 404


def test_cancel_booking(client, db):
    tour = make_tour(db, clorian_booking_id="B-TOUR-4")
    db.commit()

    create_resp = client.post("/bookings", json={
        "customer_id": "CUST-004",
        "tour_id": tour.id,
        "date": "2026-03-02",
        "adult_tickets": 1,
        "child_tickets": 1,
    })
    booking_id = create_resp.json()["booking_id"]

    resp = client.patch(f"/bookings/{booking_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_booking_not_found(client, db):
    resp = client.patch("/bookings/9999/cancel")
    assert resp.status_code == 404
