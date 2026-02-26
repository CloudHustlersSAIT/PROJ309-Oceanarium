"""Unit tests for SQLAlchemy model relationships and constraints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import date, time, datetime, timezone

from app.models.audit_log import TourAssignmentLog
from app.models.booking import Booking
from app.models.booking_version import BookingVersion
from app.models.cost import Cost
from app.models.customer import Customer
from app.models.issue import Issue
from app.models.poll_execution import PollExecution
from app.models.resource import Resource
from app.models.schedule import Schedule
from app.models.survey import Survey
from app.models.sync_log import SyncLog
from app.models.tour import Tour
from app.models.user import User
from tests.conftest import (
    make_availability,
    make_booking,
    make_booking_version,
    make_cost,
    make_customer,
    make_guide,
    make_poll_execution,
    make_resource,
    make_schedule,
    make_survey,
    make_tour,
    make_user,
)


# -- Guide Relationships --


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


def test_guide_tour_types_relationship(db):
    tour1 = make_tour(db, name="Shark Dive")
    tour2 = make_tour(db, name="Dolphin Watch")
    guide = make_guide(db, tour_type_ids=[tour1.id, tour2.id])
    db.commit()
    assert len(guide.tour_types) == 2


# -- Tour --


def test_tour_creation(db):
    tour = make_tour(db)
    db.commit()
    assert tour.id is not None
    assert tour.name == "Shark Diving"
    assert tour.duration == 120


# -- Booking + BookingVersion --


def test_booking_creation_with_version(db):
    booking = make_booking(db, clorian_booking_id="CLR-BOOK-1")
    db.commit()
    assert booking.booking_id is not None
    assert booking.latest_version is not None
    assert booking.latest_version.status == "unassigned"


def test_booking_multiple_versions(db):
    booking = make_booking(db, clorian_booking_id="CLR-MULTI")
    db.flush()
    make_booking_version(
        db, booking.booking_id,
        status="assigned", start_date=date(2026, 3, 5),
    )
    db.commit()
    assert len(booking.versions) == 2
    assert booking.latest_version.status == "assigned"


def test_booking_linked_to_tour(db):
    tour = make_tour(db)
    db.flush()
    booking = make_booking(db, clorian_booking_id="CLR-LINK-1", tour_id=tour.id)
    db.commit()
    assert booking.tour_id == tour.id
    assert booking in tour.bookings


# -- PollExecution --


def test_poll_execution_creation(db):
    pe = make_poll_execution(db)
    db.commit()
    assert pe.id is not None
    assert pe.status == "success"


# -- Cost --


def test_cost_creation(db):
    tour = make_tour(db)
    db.flush()
    cost = make_cost(db, tour.id)
    db.commit()
    assert cost.id is not None
    assert cost.tour_id == tour.id
    assert float(cost.price) == 50.00


# -- Schedule --


def test_schedule_creation(db):
    guide = make_guide(db)
    booking = make_booking(db)
    db.flush()
    lv = booking.latest_version
    schedule = make_schedule(db, lv.id, guide.id)
    db.commit()
    assert schedule.id is not None
    assert schedule.guide_id == guide.id


# -- Customer --


def test_customer_creation(db):
    customer = make_customer(db)
    db.commit()
    assert customer.id is not None
    assert customer.first_name == "John"


# -- Resource --


def test_resource_creation(db):
    resource = make_resource(db)
    db.commit()
    assert resource.id is not None
    assert resource.name == "Boat"


# -- Survey --


def test_survey_creation(db):
    customer = make_customer(db)
    guide = make_guide(db)
    booking = make_booking(db)
    db.flush()
    lv = booking.latest_version
    survey = make_survey(db, customer.id, guide.id, lv.id, rating=4, comment="Great!")
    db.commit()
    assert survey.id is not None
    assert survey.rating == 4


# -- User --


def test_user_creation(db):
    user = make_user(db)
    db.commit()
    assert user.id is not None
    assert user.username == "admin"


# -- Issue --


def test_issue_creation(db):
    issue = Issue(description="Test issue")
    db.add(issue)
    db.commit()
    assert issue.id is not None
    assert issue.created_at is not None


# -- SyncLog --


def test_sync_log_defaults(db):
    sync_log = SyncLog()
    db.add(sync_log)
    db.commit()
    assert sync_log.id is not None
    assert sync_log.new_count == 0
    assert sync_log.status == "running"


# -- Availability --


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
