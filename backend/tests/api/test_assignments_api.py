"""API endpoint tests for Assignments (Phase 7d)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.conftest import make_guide, make_tour


def test_manual_assign(client, db):
    guide = make_guide(db, name="Manual Guide", email="manual@test.com")
    tour = make_tour(db, clorian_booking_id="T-ASSIGN")
    db.commit()

    resp = client.post(f"/tours/{tour.id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide.id
    assert data["status"] == "assigned"


def test_manual_assign_logs_override(client, db):
    guide = make_guide(db, name="Log Guide", email="log@test.com")
    tour = make_tour(db, clorian_booking_id="T-LOG")
    db.commit()

    client.post(f"/tours/{tour.id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })

    resp = client.get(f"/tours/{tour.id}/assignment-log")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[-1]["assignment_type"] == "manual"


def test_get_assignment_log(client, db):
    guide = make_guide(db, name="Trail Guide", email="trail@test.com")
    tour = make_tour(db, clorian_booking_id="T-TRAIL")
    db.commit()

    client.post(f"/tours/{tour.id}/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })

    resp = client.get(f"/tours/{tour.id}/assignment-log")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all("assigned_at" in entry for entry in data)
    assert all("action" in entry for entry in data)
