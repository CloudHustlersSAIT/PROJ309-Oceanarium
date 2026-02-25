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


def test_assign_tour_not_found(client, db):
    guide = make_guide(db, name="Ghost Tour", email="ghost@test.com")
    db.commit()

    resp = client.post("/tours/9999/assign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_assign_guide_not_found(client, db):
    tour = make_tour(db, clorian_booking_id="T-NOGUIDE")
    db.commit()

    resp = client.post(f"/tours/{tour.id}/assign", json={
        "guide_id": 9999,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_reassign_guide(client, db):
    guide_a = make_guide(db, name="Guide A", email="a@reassign.com")
    guide_b = make_guide(db, name="Guide B", email="b@reassign.com")
    tour = make_tour(db, clorian_booking_id="T-REASSIGN")
    db.commit()

    client.post(f"/tours/{tour.id}/assign", json={
        "guide_id": guide_a.id,
        "assigned_by": "admin@oceanarium.com",
    })

    resp = client.post(f"/tours/{tour.id}/reassign", json={
        "guide_id": guide_b.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide_b.id
    assert data["message"] == "Guide reassigned"


def test_reassign_tour_not_found(client, db):
    guide = make_guide(db, name="Reassign Ghost", email="rg@test.com")
    db.commit()

    resp = client.post("/tours/9999/reassign", json={
        "guide_id": guide.id,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_reassign_guide_not_found(client, db):
    tour = make_tour(db, clorian_booking_id="T-REASSIGN-NOGUIDE")
    db.commit()

    resp = client.post(f"/tours/{tour.id}/reassign", json={
        "guide_id": 9999,
        "assigned_by": "admin@oceanarium.com",
    })
    assert resp.status_code == 404


def test_assignment_log_tour_not_found(client, db):
    resp = client.get("/tours/9999/assignment-log")
    assert resp.status_code == 404


def test_assignment_log_empty(client, db):
    tour = make_tour(db, clorian_booking_id="T-NOLOGS")
    db.commit()

    resp = client.get(f"/tours/{tour.id}/assignment-log")
    assert resp.status_code == 200
    assert resp.json() == []
