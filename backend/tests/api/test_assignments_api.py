"""API endpoint tests for Assignments (Schedule-based)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_booking, make_guide, make_tour


def test_manual_assign(client, db):
    guide = make_guide(db, email="manual@test.com")
    tour = make_tour(db)
    booking = make_booking(db, clorian_booking_id="CLR-ASSIGN", tour_id=tour.id)
    db.commit()

    resp = client.post(f"/bookings/{booking.booking_id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide.id
    assert "schedule_id" in data


def test_assign_booking_not_found(client, db):
    guide = make_guide(db)
    db.commit()

    resp = client.post("/bookings/9999/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_assign_guide_not_found(client, db):
    booking = make_booking(db, clorian_booking_id="CLR-NOGUIDE")
    db.commit()

    resp = client.post(f"/bookings/{booking.booking_id}/assign", json={
        "guide_id": 9999,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_reassign_guide(client, db):
    guide_a = make_guide(db, email="a@reassign.com")
    guide_b = make_guide(db, email="b@reassign.com")
    tour = make_tour(db)
    booking = make_booking(db, clorian_booking_id="CLR-REASSIGN", tour_id=tour.id)
    db.commit()

    client.post(f"/bookings/{booking.booking_id}/assign", json={
        "guide_id": guide_a.id,
        "assigned_by": "admin@test.com",
    })

    resp = client.post(f"/bookings/{booking.booking_id}/reassign", json={
        "guide_id": guide_b.id,
        "assigned_by": "admin@test.com",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide_b.id


def test_get_assignment_log(client, db):
    guide = make_guide(db, email="trail@test.com")
    tour = make_tour(db)
    booking = make_booking(db, clorian_booking_id="CLR-TRAIL", tour_id=tour.id)
    db.commit()

    client.post(f"/bookings/{booking.booking_id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@test.com",
    })

    resp = client.get(f"/bookings/{booking.booking_id}/assignment-log")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


def test_assignment_log_booking_not_found(client, db):
    resp = client.get("/bookings/9999/assignment-log")
    assert resp.status_code == 404


def test_assign_booking_no_version(client, db):
    from app.models.booking import Booking
    booking = Booking(clorian_booking_id="CLR-NOVERSION")
    db.add(booking)
    db.commit()

    guide = make_guide(db)
    db.commit()

    resp = client.post(f"/bookings/{booking.booking_id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@test.com",
    })
    assert resp.status_code == 400
    assert "no version" in resp.json()["detail"].lower()


def test_reassign_booking_not_found(client, db):
    guide = make_guide(db)
    db.commit()
    resp = client.post("/bookings/9999/reassign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@test.com",
    })
    assert resp.status_code == 404


def test_reassign_booking_no_version(client, db):
    from app.models.booking import Booking
    booking = Booking(clorian_booking_id="CLR-REASSIGN-NOV")
    db.add(booking)
    db.commit()

    guide = make_guide(db)
    db.commit()

    resp = client.post(f"/bookings/{booking.booking_id}/reassign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@test.com",
    })
    assert resp.status_code == 400


def test_reassign_guide_not_found(client, db):
    booking = make_booking(db, clorian_booking_id="CLR-REASSIGN-NG")
    db.commit()

    resp = client.post(f"/bookings/{booking.booking_id}/reassign", json={
        "guide_id": 9999,
        "assigned_by": "admin@test.com",
    })
    assert resp.status_code == 404


def test_assignment_log_no_tour(client, db):
    booking = make_booking(db, clorian_booking_id="CLR-NOTOUR")
    db.commit()

    resp = client.get(f"/bookings/{booking.booking_id}/assignment-log")
    assert resp.status_code == 200
    assert resp.json() == []
