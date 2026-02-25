"""API endpoint tests for Tours (Phase 7d)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_tour


def test_list_tours(client, db):
    make_tour(db, clorian_booking_id="T-1")
    make_tour(db, clorian_booking_id="T-2")
    db.commit()

    resp = client.get("/tours")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_unassigned_tours(client, db):
    make_tour(db, clorian_booking_id="T-A", status="assigned")
    make_tour(db, clorian_booking_id="T-U", status="unassigned")
    db.commit()

    resp = client.get("/tours/unassigned")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "unassigned"


def test_get_tour_detail(client, db):
    tour = make_tour(db, clorian_booking_id="T-DETAIL")
    db.commit()

    resp = client.get(f"/tours/{tour.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["clorian_booking_id"] == "T-DETAIL"
    assert "assigned_guide_name" in data


def test_get_tour_not_found(client, db):
    resp = client.get("/tours/9999")
    assert resp.status_code == 404


def test_list_tours_empty(client, db):
    resp = client.get("/tours")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_unassigned_tours_empty(client, db):
    resp = client.get("/tours/unassigned")
    assert resp.status_code == 200
    assert resp.json() == []


def test_tour_with_assigned_guide_name(client, db):
    from tests.conftest import make_guide

    guide = make_guide(db, name="Tour Guide", email="tourguide@test.com")
    tour = make_tour(
        db, clorian_booking_id="T-NAMED",
        status="assigned", assigned_guide_id=guide.id,
    )
    db.commit()

    resp = client.get(f"/tours/{tour.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_guide_name"] == "Tour Guide"
    assert data["assigned_guide_id"] == guide.id


def test_list_tours_ordered_by_date(client, db):
    from datetime import date, time

    make_tour(db, clorian_booking_id="T-LATE", tour_date=date(2026, 3, 5),
              start_time=time(9, 0), end_time=time(11, 0))
    make_tour(db, clorian_booking_id="T-EARLY", tour_date=date(2026, 3, 1),
              start_time=time(9, 0), end_time=time(11, 0))
    db.commit()

    resp = client.get("/tours")
    data = resp.json()
    assert len(data) == 2
    assert data[0]["clorian_booking_id"] == "T-EARLY"
    assert data[1]["clorian_booking_id"] == "T-LATE"
