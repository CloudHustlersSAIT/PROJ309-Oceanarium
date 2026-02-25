"""Unit tests for Pydantic schema validation."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from pydantic import ValidationError

from app.schemas.guide import (
    AvailabilityExceptionIn,
    AvailabilitySetIn,
    AvailabilitySlotIn,
    GuideCreate,
    GuideUpdate,
)
from app.schemas.tour import ManualAssignIn
from app.schemas.booking import BookingCreate, BookingReschedule


# ── GuideCreate ──────────────────────────────────────────────────────


def test_guide_create_valid():
    guide = GuideCreate(name="Ana", email="ana@test.com")
    assert guide.name == "Ana"
    assert guide.is_active is True
    assert guide.languages == []
    assert guide.expertises == []


def test_guide_create_with_all_fields():
    guide = GuideCreate(
        name="Ana",
        email="ana@test.com",
        is_active=False,
        languages=["en", "pt"],
        expertises=["Sharks"],
    )
    assert guide.is_active is False
    assert len(guide.languages) == 2


def test_guide_create_missing_name():
    with pytest.raises(ValidationError):
        GuideCreate(email="a@b.com")


def test_guide_create_missing_email():
    with pytest.raises(ValidationError):
        GuideCreate(name="Ana")


# ── GuideUpdate ──────────────────────────────────────────────────────


def test_guide_update_all_optional():
    update = GuideUpdate()
    assert update.name is None
    assert update.email is None
    assert update.is_active is None
    assert update.languages is None
    assert update.expertises is None


def test_guide_update_partial():
    update = GuideUpdate(name="New Name")
    assert update.name == "New Name"
    assert update.email is None


# ── AvailabilitySlotIn / AvailabilityExceptionIn / AvailabilitySetIn ─


def test_availability_slot_valid():
    slot = AvailabilitySlotIn(day_of_week=0, start_time="08:00", end_time="17:00")
    assert slot.day_of_week == 0


def test_availability_slot_missing_fields():
    with pytest.raises(ValidationError):
        AvailabilitySlotIn(day_of_week=0)


def test_availability_exception_valid():
    exc = AvailabilityExceptionIn(date="2026-03-15", type="blocked", reason="Holiday")
    assert exc.type == "blocked"


def test_availability_exception_optional_reason():
    exc = AvailabilityExceptionIn(date="2026-03-15", type="note")
    assert exc.reason is None


def test_availability_set_defaults():
    avail = AvailabilitySetIn()
    assert avail.timezone == "UTC"
    assert avail.slots == []
    assert avail.exceptions == []


# ── ManualAssignIn ───────────────────────────────────────────────────


def test_manual_assign_valid():
    payload = ManualAssignIn(guide_id=1, assigned_by="admin@test.com")
    assert payload.guide_id == 1


def test_manual_assign_missing_guide_id():
    with pytest.raises(ValidationError):
        ManualAssignIn(assigned_by="admin@test.com")


def test_manual_assign_missing_assigned_by():
    with pytest.raises(ValidationError):
        ManualAssignIn(guide_id=1)


# ── BookingCreate / BookingReschedule ────────────────────────────────


def test_booking_create_valid():
    booking = BookingCreate(
        clorian_booking_id="CLR-1",
        date="2026-03-02",
        start_time="09:00:00",
        end_time="11:00:00",
    )
    assert booking.clorian_booking_id == "CLR-1"
    assert booking.adult_tickets == 0
    assert booking.child_tickets == 0


def test_booking_create_with_all_fields():
    booking = BookingCreate(
        clorian_booking_id="CLR-2",
        date="2026-03-02",
        start_time="09:00:00",
        end_time="11:00:00",
        required_expertise="Sharks",
        required_category="Marine Biology",
        requested_language_code="en",
        customer_id="CUST-1",
        adult_tickets=2,
        child_tickets=1,
    )
    assert booking.customer_id == "CUST-1"
    assert booking.adult_tickets == 2


def test_booking_create_missing_fields():
    with pytest.raises(ValidationError):
        BookingCreate(clorian_booking_id="CLR-1")


def test_booking_reschedule_valid():
    reschedule = BookingReschedule(new_date="2026-03-10")
    assert str(reschedule.new_date) == "2026-03-10"


def test_booking_reschedule_missing_date():
    with pytest.raises(ValidationError):
        BookingReschedule()
