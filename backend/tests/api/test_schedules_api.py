"""API endpoint tests for Schedules."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_booking, make_guide, make_resource


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


def test_delete_schedule_not_found(client, db):
    resp = client.delete("/schedules/9999")
    assert resp.status_code == 404


def test_filter_schedules_by_guide(client, db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    resp = client.get(f"/schedules?guide_id={guide.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp_empty = client.get("/schedules?guide_id=9999")
    assert resp_empty.json() == []


def test_filter_schedules_by_booking_version(client, db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    resp = client.get(f"/schedules?booking_version_id={lv.id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_schedule(client, db):
    guide_a = make_guide(db, email="a@sched.com")
    guide_b = make_guide(db, email="b@sched.com")
    resource = make_resource(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    create = client.post("/schedules", json={
        "booking_version_id": lv.id,
        "guide_id": guide_a.id,
        "start_date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T11:00:00",
    })
    schedule_id = create.json()["id"]
    resp = client.patch(f"/schedules/{schedule_id}", json={
        "guide_id": guide_b.id,
        "resource_id": resource.id,
        "start_date": "2026-03-03T10:00:00",
        "end_date": "2026-03-03T12:00:00",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide_b.id


def test_update_schedule_not_found(client, db):
    resp = client.patch("/schedules/9999", json={"guide_id": 1})
    assert resp.status_code == 404
