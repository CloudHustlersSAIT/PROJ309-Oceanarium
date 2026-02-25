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
