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
from app.schemas.tour import ManualAssignIn, TourCreate
from app.schemas.booking import BookingCreate, BookingReschedule, BookingVersionCreate
from app.schemas.cost import CostCreate
from app.schemas.schedule import ScheduleCreate
from app.schemas.customer import CustomerCreate
from app.schemas.resource import ResourceCreate
from app.schemas.survey import SurveyCreate
from app.schemas.user import UserCreate


# -- GuideCreate --


def test_guide_create_valid():
    guide = GuideCreate(first_name="Ana", last_name="Costa", email="ana@test.com")
    assert guide.first_name == "Ana"
    assert guide.is_active is True
    assert guide.languages == []
    assert guide.expertises == []


def test_guide_create_with_all_fields():
    guide = GuideCreate(
        first_name="Ana",
        last_name="Costa",
        email="ana@test.com",
        phone="+351999",
        guide_rating=4.5,
        is_active=False,
        languages=["en", "pt"],
        expertises=[],
    )
    assert guide.is_active is False
    assert len(guide.languages) == 2


def test_guide_create_missing_first_name():
    with pytest.raises(ValidationError):
        GuideCreate(last_name="Costa", email="a@b.com")


def test_guide_create_missing_email():
    with pytest.raises(ValidationError):
        GuideCreate(first_name="Ana", last_name="Costa")


# -- GuideUpdate --


def test_guide_update_all_optional():
    update = GuideUpdate()
    assert update.first_name is None
    assert update.last_name is None
    assert update.email is None


def test_guide_update_partial():
    update = GuideUpdate(first_name="New Name")
    assert update.first_name == "New Name"
    assert update.email is None


# -- Availability --


def test_availability_slot_valid():
    slot = AvailabilitySlotIn(day_of_week=0, start_time="08:00", end_time="17:00")
    assert slot.day_of_week == 0


def test_availability_slot_missing_fields():
    with pytest.raises(ValidationError):
        AvailabilitySlotIn(day_of_week=0)


def test_availability_exception_valid():
    exc = AvailabilityExceptionIn(date="2026-03-15", type="blocked", reason="Holiday")
    assert exc.type == "blocked"


def test_availability_set_defaults():
    avail = AvailabilitySetIn()
    assert avail.timezone == "UTC"
    assert avail.slots == []


# -- ManualAssignIn --


def test_manual_assign_valid():
    payload = ManualAssignIn(guide_id=1, assigned_by="admin@test.com")
    assert payload.guide_id == 1


def test_manual_assign_missing_guide_id():
    with pytest.raises(ValidationError):
        ManualAssignIn(assigned_by="admin@test.com")


# -- TourCreate --


def test_tour_create_valid():
    tour = TourCreate(name="Shark Dive", description="Exciting!", duration=90)
    assert tour.name == "Shark Dive"


def test_tour_create_all_optional():
    tour = TourCreate()
    assert tour.name is None
    assert tour.duration is None


# -- BookingCreate --


def test_booking_create_valid():
    booking = BookingCreate(
        clorian_booking_id="CLR-1",
        start_date="2026-03-02",
    )
    assert booking.clorian_booking_id == "CLR-1"
    assert booking.adult_tickets == 0
    assert booking.child_tickets == 0


def test_booking_create_with_all_fields():
    booking = BookingCreate(
        clorian_booking_id="CLR-2",
        customer_id=1,
        tour_id=1,
        status="unassigned",
        adult_tickets=2,
        child_tickets=1,
        start_date="2026-03-02",
    )
    assert booking.customer_id == 1
    assert booking.adult_tickets == 2


def test_booking_create_missing_fields():
    with pytest.raises(ValidationError):
        BookingCreate(clorian_booking_id="CLR-1")


def test_booking_reschedule_valid():
    reschedule = BookingReschedule(new_date="2026-03-10")
    assert str(reschedule.new_date) == "2026-03-10"


def test_booking_version_create_valid():
    bv = BookingVersionCreate(start_date="2026-03-02", adult_tickets=2, child_tickets=1)
    assert bv.status == "unassigned"


# -- CostCreate --


def test_cost_create_valid():
    cost = CostCreate(
        tour_id=1,
        ticket_type="adult",
        price=50.00,
        valid_from="2026-01-01T00:00:00",
        valid_to="2026-12-31T23:59:59",
    )
    assert cost.ticket_type == "adult"


# -- ScheduleCreate --


def test_schedule_create_valid():
    sched = ScheduleCreate(
        booking_version_id=1,
        guide_id=1,
        start_date="2026-03-02T09:00:00",
        end_date="2026-03-02T11:00:00",
    )
    assert sched.guide_id == 1


# -- CustomerCreate --


def test_customer_create_valid():
    c = CustomerCreate(first_name="John", last_name="Doe", email="john@test.com")
    assert c.phone is None


# -- ResourceCreate --


def test_resource_create_valid():
    r = ResourceCreate(name="Boat", type="vehicle", quantity_available=5)
    assert r.name == "Boat"


# -- SurveyCreate --


def test_survey_create_valid():
    s = SurveyCreate(customer_id=1, guide_id=1, booking_version_id=1, rating=5)
    assert s.comment is None


def test_survey_create_missing_rating():
    with pytest.raises(ValidationError):
        SurveyCreate(customer_id=1, guide_id=1, booking_version_id=1)


# -- UserCreate --


def test_user_create_valid():
    u = UserCreate(
        username="admin",
        email="admin@test.com",
        password_hash="hash",
        full_name="Admin",
        role="admin",
    )
    assert u.is_active is True
