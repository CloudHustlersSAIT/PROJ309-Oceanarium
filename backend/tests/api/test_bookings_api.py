"""API endpoint tests for Bookings."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _booking_payload(**overrides):
    defaults = {
        "clorian_booking_id": "CLR-API-001",
        "date": "2026-03-02",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "required_expertise": "Sharks",
        "required_category": "Marine Biology",
        "requested_language_code": "en",
        "adult_tickets": 2,
        "child_tickets": 1,
    }
    defaults.update(overrides)
    return defaults


def test_list_bookings_empty(client, db):
    resp = client.get("/bookings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_booking(client, db):
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["clorian_booking_id"] == "CLR-API-001"
    assert data["status"] == "pending"
    assert data["tour_id"] is None
    assert data["adult_tickets"] == 2
    assert data["child_tickets"] == 1


def test_create_booking_duplicate_rejected(client, db):
    client.post("/bookings", json=_booking_payload())
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.status_code == 409


def test_list_bookings_after_create(client, db):
    client.post("/bookings", json=_booking_payload())

    resp = client.get("/bookings")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["clorian_booking_id"] == "CLR-API-001"


def test_list_bookings_filter_by_status(client, db):
    client.post("/bookings", json=_booking_payload(clorian_booking_id="CLR-A"))
    client.post("/bookings", json=_booking_payload(clorian_booking_id="CLR-B"))

    bid = client.get("/bookings").json()[0]["booking_id"]
    client.patch(f"/bookings/{bid}/cancel")

    resp_pending = client.get("/bookings?status=pending")
    assert len(resp_pending.json()) == 1

    resp_cancelled = client.get("/bookings?status=cancelled")
    assert len(resp_cancelled.json()) == 1


def test_list_unassigned_bookings(client, db):
    client.post("/bookings", json=_booking_payload(clorian_booking_id="CLR-U1"))
    client.post("/bookings", json=_booking_payload(clorian_booking_id="CLR-U2"))

    resp = client.get("/bookings/unassigned")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_reschedule_booking(client, db):
    create_resp = client.post("/bookings", json=_booking_payload())
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
    create_resp = client.post("/bookings", json=_booking_payload())
    booking_id = create_resp.json()["booking_id"]

    resp = client.patch(f"/bookings/{booking_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_booking_not_found(client, db):
    resp = client.patch("/bookings/9999/cancel")
    assert resp.status_code == 404
