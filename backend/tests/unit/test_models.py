"""Unit tests for SQLAlchemy model relationships and constraints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import date, time

from app.models.audit_log import TourAssignmentLog
from app.models.booking import Booking
from app.models.issue import Issue
from app.models.sync_log import SyncLog
from tests.conftest import make_availability, make_guide, make_tour


# ── Guide Relationships ─────────────────────────────────────────────


def test_guide_languages_relationship(db):
    guide = make_guide(db, language_codes=["en", "pt", "fr"])
    db.commit()
    assert len(guide.languages) == 3
    assert {lang.code for lang in guide.languages} == {"en", "pt", "fr"}


def test_guide_expertises_relationship(db):
    guide = make_guide(
        db,
        expertise_names=["Sharks", "Dolphins"],
        expertise_categories=["Marine Biology", "Marine Biology"],
    )
    db.commit()
    assert len(guide.expertises) == 2
    assert {exp.name for exp in guide.expertises} == {"Sharks", "Dolphins"}


def test_guide_availability_relationship(db):
    guide = make_guide(db)
    make_availability(
        db, guide,
        slots=[{"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)}],
    )
    db.commit()
    assert guide.availability_pattern is not None
    assert guide.availability_pattern.timezone == "UTC"
    assert len(guide.availability_pattern.slots) == 1


def test_guide_without_availability(db):
    guide = make_guide(db)
    db.commit()
    assert guide.availability_pattern is None


def test_guide_assigned_tours_relationship(db):
    guide = make_guide(db)
    make_tour(db, clorian_booking_id="T-R1", status="assigned", assigned_guide_id=guide.id)
    make_tour(db, clorian_booking_id="T-R2", status="assigned", assigned_guide_id=guide.id)
    db.commit()
    assert len(guide.assigned_tours) == 2


# ── Tour Relationships ──────────────────────────────────────────────


def test_tour_assigned_guide_relationship(db):
    guide = make_guide(db)
    tour = make_tour(db, clorian_booking_id="T-REL", status="assigned", assigned_guide_id=guide.id)
    db.commit()
    assert tour.assigned_guide is not None
    assert tour.assigned_guide.id == guide.id


def test_tour_without_guide(db):
    tour = make_tour(db, clorian_booking_id="T-NOGUIDE")
    db.commit()
    assert tour.assigned_guide is None


def test_tour_assignment_logs_relationship(db):
    guide = make_guide(db)
    tour = make_tour(db, clorian_booking_id="T-LOGS")
    db.commit()

    log = TourAssignmentLog(
        tour_id=tour.id,
        guide_id=guide.id,
        assignment_type="manual",
        action="assigned",
        assigned_by="admin@test.com",
    )
    db.add(log)
    db.commit()

    assert len(tour.assignment_logs) == 1
    assert tour.assignment_logs[0].action == "assigned"


# ── Availability Relationships ──────────────────────────────────────


def test_availability_pattern_slots_and_exceptions(db):
    guide = make_guide(db)
    pattern = make_availability(
        db, guide,
        slots=[
            {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
            {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(17, 0)},
        ],
        exceptions=[
            {"date": date(2026, 3, 15), "type": "blocked", "reason": "Holiday"},
        ],
    )
    db.commit()
    assert len(pattern.slots) == 2
    assert len(pattern.exceptions) == 1
    assert pattern.exceptions[0].reason == "Holiday"


def test_availability_slot_back_populates_pattern(db):
    guide = make_guide(db)
    pattern = make_availability(
        db, guide,
        slots=[{"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)}],
    )
    db.commit()
    slot = pattern.slots[0]
    assert slot.pattern.id == pattern.id


# ── Booking Model ───────────────────────────────────────────────────


def test_booking_creation(db):
    booking = Booking(
        clorian_booking_id="CLR-BOOK-1",
        date=date(2026, 3, 2),
        start_time=time(9, 0),
        end_time=time(11, 0),
        required_expertise="Sharks",
        required_category="Marine Biology",
        requested_language_code="en",
    )
    db.add(booking)
    db.commit()
    assert booking.booking_id is not None
    assert booking.status == "pending"
    assert booking.tour_id is None
    assert booking.created_at is not None


def test_booking_linked_to_tour(db):
    tour = make_tour(db, clorian_booking_id="T-LINK")
    db.flush()
    booking = Booking(
        clorian_booking_id="CLR-LINK-1",
        date=date(2026, 3, 2),
        start_time=time(9, 0),
        end_time=time(11, 0),
        tour_id=tour.id,
        status="assigned",
    )
    db.add(booking)
    db.commit()
    assert booking.tour_id == tour.id
    assert tour.booking is not None
    assert tour.booking.booking_id == booking.booking_id


# ── Issue Model ─────────────────────────────────────────────────────


def test_issue_creation(db):
    issue = Issue(description="Test issue")
    db.add(issue)
    db.commit()
    assert issue.id is not None
    assert issue.created_at is not None


# ── SyncLog Model ──────────────────────────────────────────────────


def test_sync_log_defaults(db):
    sync_log = SyncLog()
    db.add(sync_log)
    db.commit()
    assert sync_log.id is not None
    assert sync_log.new_count == 0
    assert sync_log.changed_count == 0
    assert sync_log.cancelled_count == 0
    assert sync_log.status == "running"
