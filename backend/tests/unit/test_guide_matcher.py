"""Unit tests for the guide matching algorithm.

Covers availability rules and tour-type matching using BookingVersion.
"""
from datetime import date, time

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.schedule import Schedule
from app.services.guide_matcher import find_eligible_guides
from tests.conftest import (
    make_availability,
    make_booking,
    make_booking_version,
    make_guide,
    make_schedule,
    make_tour,
)


# -- Availability Rule Tests --


def test_available_guide_is_eligible(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1
    assert result[0].id == guide.id


def test_inactive_guide_excluded(db):
    guide = make_guide(db, is_active=False)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


def test_guide_without_slot_for_day_excluded(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 3))  # Tuesday
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


def test_blocking_exception_excludes_guide(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ], exceptions=[
        {"date": date(2026, 3, 2), "type": "blocked", "reason": "Personal leave"},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


def test_non_blocking_exception_keeps_guide(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ], exceptions=[
        {"date": date(2026, 3, 2), "type": "note", "reason": "Dentist at 15:00"},
    ])
    booking = make_booking(db, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1


def test_overlapping_schedule_excludes_guide(db):
    from datetime import datetime as dt

    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking1 = make_booking(db, clorian_booking_id="EXISTING", booking_date=date(2026, 3, 2))
    db.flush()
    lv = booking1.latest_version
    schedule = Schedule(
        booking_version_id=lv.id,
        guide_id=guide.id,
        start_date=dt(2026, 3, 2, 9, 0),
        end_date=dt(2026, 3, 2, 11, 0),
    )
    db.add(schedule)
    db.flush()

    booking2 = make_booking(db, clorian_booking_id="NEW", booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking2.latest_version, db)
    assert len(result) == 0


def test_guide_without_availability_pattern_excluded(db):
    make_guide(db)
    booking = make_booking(db)
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


# -- Tour Type Matching --


def test_guide_with_matching_tour_type_eligible(db):
    tour = make_tour(db, name="Shark Dive")
    guide = make_guide(db, tour_type_ids=[tour.id])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, tour_id=tour.id, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1


def test_guide_without_matching_tour_type_excluded(db):
    tour_a = make_tour(db, name="Shark Dive")
    tour_b = make_tour(db, name="Dolphin Watch")
    guide = make_guide(db, tour_type_ids=[tour_b.id])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, tour_id=tour_a.id, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


def test_booking_without_tour_skips_tour_type_check(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(db, tour_id=None, booking_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1


# -- Language Matching --


def test_guide_with_matching_language_eligible(db):
    guide = make_guide(db, language_codes=["en", "pt"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(
        db, booking_date=date(2026, 3, 2), requested_language_code="pt",
    )
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1


def test_guide_without_matching_language_excluded(db):
    guide = make_guide(db, language_codes=["en"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(
        db, booking_date=date(2026, 3, 2), requested_language_code="fr",
    )
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 0


def test_booking_without_language_skips_language_check(db):
    guide = make_guide(db, language_codes=["en"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    booking = make_booking(
        db, booking_date=date(2026, 3, 2), requested_language_code=None,
    )
    db.commit()

    result = find_eligible_guides(booking.latest_version, db)
    assert len(result) == 1
