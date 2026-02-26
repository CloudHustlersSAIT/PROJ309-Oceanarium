"""API endpoint tests for Schedules."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_booking, make_guide


def test_list_schedules_empty(client, db):
    resp = client.get("/schedules")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_schedule(client, db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    resp = client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["guide_id"] == guide.id


def test_get_schedule(client, db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    schedule_id = create.json()["id"]
    resp = client.get(f"/schedules/{schedule_id}")
    assert resp.status_code == 200


def test_get_schedule_not_found(client, db):
    resp = client.get("/schedules/9999")
    assert resp.status_code == 404


def test_delete_schedule(client, db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    schedule_id = create.json()["id"]
    resp = client.delete(f"/schedules/{schedule_id}")
    assert resp.status_code == 204
