"""API endpoint tests for Bookings."""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _booking_payload(**overrides):
    defaults = {
        "clorian_booking_id": "CLR-API-001",
        "start_date": "2026-03-02",
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
    assert data["status"] == "unassigned"
    assert data["adult_tickets"] == 2
    assert data["child_tickets"] == 1
    assert data["date"] == "2026-03-02"


def test_create_booking_duplicate_rejected(client, db):
    client.post("/bookings", json=_booking_payload())
    resp = client.post("/bookings", json=_booking_payload())
    assert resp.status_code == 409


def test_create_booking_returns_language_code(client, db):
    from tests.conftest import make_booking

    booking = make_booking(db, requested_language_code="pt")
    db.commit()

    resp = client.get("/bookings")
    assert resp.status_code == 200
    data = resp.json()
    match = [b for b in data if b["booking_id"] == booking.booking_id]
    assert len(match) == 1
    assert match[0]["requested_language_code"] == "pt"


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

    resp_pending = client.get("/bookings?status=unassigned")
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


def test_reschedule_assigned_booking_guide_unavailable(client, db):
    """Rescheduling to a day the guide can't work resets status to pending."""
    from datetime import time

    from app.models.schedule import Schedule
    from app.services.assignment import assign_guide_to_booking
    from tests.conftest import make_availability, make_booking, make_guide

    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))  # Monday
    db.commit()

    lv = booking.latest_version
    assign_guide_to_booking(lv, guide, db)
    db.commit()

    assert booking.latest_version.status == "assigned"

    resp = client.patch(
        f"/bookings/{booking.booking_id}/reschedule",
        json={"new_date": "2026-03-03"},  # Tuesday — guide has no slot
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "unassigned"
    assert resp.json()["guide_name"] is None

    remaining = db.query(Schedule).all()
    assert len(remaining) == 0


def test_reschedule_assigned_booking_guide_available(client, db):
    """Rescheduling to a day the guide can work keeps status assigned."""
    from datetime import time

    from app.models.schedule import Schedule
    from app.services.assignment import assign_guide_to_booking
    from tests.conftest import make_availability, make_booking, make_guide

    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))  # Monday
    db.commit()

    lv = booking.latest_version
    assign_guide_to_booking(lv, guide, db)
    db.commit()

    assert booking.latest_version.status == "assigned"

    resp = client.patch(
        f"/bookings/{booking.booking_id}/reschedule",
        json={"new_date": "2026-03-09"},  # Next Monday — guide is available
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "assigned"
    assert resp.json()["guide_name"] is not None

    schedules = db.query(Schedule).all()
    assert len(schedules) == 1


def test_create_booking_triggers_auto_assignment(client, db):
    """Creating a booking auto-assigns an eligible guide."""
    from tests.conftest import make_availability, make_guide

    guide = make_guide(db, email="auto@test.com")
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": "08:00", "end_time": "17:00"},
    ])
    db.commit()

    resp = client.post("/bookings", json=_booking_payload(
        clorian_booking_id="CLR-AUTOASSIGN",
        start_date="2026-03-02",
    ))
    assert resp.status_code == 201
    assert resp.json()["status"] == "assigned"
    assert resp.json()["guide_name"] is not None


def test_reschedule_triggers_auto_assignment(client, db):
    """Rescheduling an unassigned booking to a date with an eligible guide auto-assigns."""
    from tests.conftest import make_availability, make_guide

    guide = make_guide(db, email="resch-auto@test.com")
    make_availability(db, guide, slots=[
        {"day_of_week": 1, "start_time": "08:00", "end_time": "17:00"},
    ])
    db.commit()

    resp = client.post("/bookings", json=_booking_payload(
        clorian_booking_id="CLR-RESCHAUTO",
        start_date="2026-03-04",  # Wednesday — no guide available
    ))
    assert resp.status_code == 201
    assert resp.json()["status"] == "unassigned"

    booking_id = resp.json()["booking_id"]
    resp = client.patch(f"/bookings/{booking_id}/reschedule", json={
        "new_date": "2026-03-03",  # Tuesday — guide is available
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "assigned"
    assert resp.json()["guide_name"] is not None


def test_cancel_frees_guide_for_other_bookings(client, db):
    """Cancelling a booking frees the guide so another pending booking gets assigned."""
    from datetime import time

    from app.services.assignment import assign_guide_to_booking
    from tests.conftest import make_availability, make_booking, make_guide

    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)},
    ])
    booking_a = make_booking(db, clorian_booking_id="CLR-CANCEL-A", booking_date=date(2026, 3, 2))
    booking_b = make_booking(db, clorian_booking_id="CLR-CANCEL-B", booking_date=date(2026, 3, 2))
    db.commit()

    lv = booking_a.latest_version
    assign_guide_to_booking(lv, guide, db)
    db.commit()

    assert booking_a.latest_version.status == "assigned"
    assert booking_b.latest_version.status == "unassigned"

    resp = client.patch(f"/bookings/{booking_a.booking_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    db.refresh(booking_b)
    assert booking_b.latest_version.status == "assigned"
