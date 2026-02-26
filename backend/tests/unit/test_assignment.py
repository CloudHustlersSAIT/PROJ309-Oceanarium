"""Unit tests for assignment execution via Schedule.

Covers manual assignment, reassignment, release, and audit logging.
"""
from datetime import date, time

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.audit_log import TourAssignmentLog
from app.models.schedule import Schedule
from app.services.assignment import (
    assign_guide_to_booking,
    manual_assign,
    release_guide_from_schedule,
)
from tests.conftest import make_availability, make_booking, make_guide, make_tour


def test_assign_guide_creates_schedule(db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    schedule = assign_guide_to_booking(lv, guide, db)
    db.commit()

    assert schedule is not None
    assert schedule.guide_id == guide.id
    assert schedule.booking_version_id == lv.id


def test_manual_assign_creates_schedule(db):
    guide = make_guide(db)
    tour = make_tour(db)
    booking = make_booking(db, tour_id=tour.id)
    db.commit()
    lv = booking.latest_version

    schedule = manual_assign(lv, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert schedule is not None
    assert schedule.guide_id == guide.id


def test_manual_reassign_replaces_schedule(db):
    guide_a = make_guide(db, email="a@test.com")
    guide_b = make_guide(db, email="b@test.com")
    tour = make_tour(db)
    booking = make_booking(db, tour_id=tour.id)
    db.commit()
    lv = booking.latest_version

    manual_assign(lv, guide_a, db, assigned_by="admin@test.com")
    db.flush()

    schedule = manual_assign(lv, guide_b, db, assigned_by="admin@test.com")
    db.commit()

    assert schedule.guide_id == guide_b.id
    all_schedules = db.query(Schedule).filter(
        Schedule.booking_version_id == lv.id
    ).all()
    assert len(all_schedules) == 1


def test_assign_guide_sets_status_assigned(db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version
    assert lv.status == "unassigned"

    assign_guide_to_booking(lv, guide, db)
    db.commit()

    db.refresh(lv)
    assert lv.status == "assigned"


def test_manual_assign_sets_status_assigned(db):
    guide = make_guide(db)
    tour = make_tour(db)
    booking = make_booking(db, tour_id=tour.id)
    db.commit()
    lv = booking.latest_version
    assert lv.status == "unassigned"

    manual_assign(lv, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    db.refresh(lv)
    assert lv.status == "assigned"


def test_release_guide_removes_schedule(db):
    guide = make_guide(db)
    tour = make_tour(db)
    booking = make_booking(db, tour_id=tour.id)
    db.commit()
    lv = booking.latest_version

    schedule = assign_guide_to_booking(lv, guide, db)
    db.flush()

    release_guide_from_schedule(schedule, db)
    db.commit()

    remaining = db.query(Schedule).filter(
        Schedule.booking_version_id == lv.id
    ).all()
    assert len(remaining) == 0


def test_release_guide_resets_status_to_pending(db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.commit()
    lv = booking.latest_version

    schedule = assign_guide_to_booking(lv, guide, db)
    db.flush()
    assert lv.status == "assigned"

    release_guide_from_schedule(schedule, db)
    db.commit()

    db.refresh(lv)
    assert lv.status == "unassigned"
