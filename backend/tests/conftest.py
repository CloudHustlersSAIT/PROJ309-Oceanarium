import os
from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DEFAULT_TEST_DB = "postgresql+psycopg2://postgres:postgres@localhost:5432/oceanarium_test"
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)

os.environ.setdefault("DATABASE_URL", TEST_DB_URL)

from app.db import Base, get_db
from app.models.availability import (
    AvailabilityException,
    AvailabilityPattern,
    AvailabilitySlot,
)
from app.models.booking import Booking
from app.models.booking_version import BookingVersion
from app.models.cost import Cost
from app.models.customer import Customer
from app.models.guide import Guide, Language
from app.models.issue import Issue
from app.models.poll_execution import PollExecution
from app.models.resource import Resource
from app.models.schedule import Schedule
from app.models.survey import Survey
from app.models.tour import Tour
from app.models.user import User

engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        engine.dispose()


@pytest.fixture
def client(db):
    from app.main import create_app

    app = create_app()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


def make_guide(
    db,
    first_name="Test",
    last_name="Guide",
    email=None,
    phone="",
    guide_rating=0,
    is_active=True,
    language_codes=None,
    tour_type_ids=None,
):
    if email is None:
        import uuid
        email = f"{uuid.uuid4().hex[:8]}@test.com"
    if language_codes is None:
        language_codes = ["en"]

    guide = Guide(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        guide_rating=guide_rating,
        is_active=is_active,
    )
    db.add(guide)
    db.flush()

    for code in language_codes:
        lang = db.query(Language).filter(Language.code == code).first()
        if not lang:
            lang = Language(code=code, name=code)
            db.add(lang)
            db.flush()
        guide.languages.append(lang)

    if tour_type_ids:
        for tid in tour_type_ids:
            tour = db.query(Tour).filter(Tour.id == tid).first()
            if tour:
                guide.tour_types.append(tour)

    db.flush()
    return guide


def make_availability(
    db,
    guide,
    timezone_str="UTC",
    slots=None,
    exceptions=None,
):
    pattern = AvailabilityPattern(guide_id=guide.id, timezone=timezone_str)
    db.add(pattern)
    db.flush()

    if slots:
        for s in slots:
            slot = AvailabilitySlot(
                pattern_id=pattern.id,
                day_of_week=s["day_of_week"],
                start_time=s["start_time"],
                end_time=s["end_time"],
            )
            db.add(slot)

    if exceptions:
        for e in exceptions:
            exc = AvailabilityException(
                pattern_id=pattern.id,
                date=e["date"],
                type=e["type"],
                reason=e.get("reason"),
            )
            db.add(exc)

    db.flush()
    return pattern


def make_tour(
    db,
    name="Shark Diving",
    description="An exciting shark tour",
    duration=120,
):
    tour = Tour(
        name=name,
        description=description,
        duration=duration,
    )
    db.add(tour)
    db.flush()
    return tour


def make_booking(
    db,
    clorian_booking_id=None,
    customer_id=None,
    tour_id=None,
    booking_date=None,
    adult_tickets=0,
    child_tickets=0,
    status="unassigned",
    requested_language_code=None,
):
    if clorian_booking_id is None:
        import uuid
        clorian_booking_id = f"CLR-{uuid.uuid4().hex[:6]}"
    if booking_date is None:
        booking_date = date(2026, 3, 2)

    booking = Booking(
        clorian_booking_id=clorian_booking_id,
        customer_id=customer_id,
        tour_id=tour_id,
        requested_language_code=requested_language_code,
    )
    db.add(booking)
    db.flush()

    import hashlib
    raw = f"{booking.booking_id}|{status}|{adult_tickets}|{child_tickets}|{booking_date}"
    version_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    version = BookingVersion(
        booking_id=booking.booking_id,
        hash=version_hash,
        status=status,
        adult_tickets=adult_tickets,
        child_tickets=child_tickets,
        start_date=booking_date,
        valid_from=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()

    return booking


def make_booking_version(
    db,
    booking_id,
    status="unassigned",
    adult_tickets=0,
    child_tickets=0,
    start_date=None,
    poll_execution_id=None,
):
    if start_date is None:
        start_date = date(2026, 3, 2)

    import hashlib
    raw = f"{booking_id}|{status}|{adult_tickets}|{child_tickets}|{start_date}"
    version_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    version = BookingVersion(
        booking_id=booking_id,
        hash=version_hash,
        status=status,
        adult_tickets=adult_tickets,
        child_tickets=child_tickets,
        start_date=start_date,
        valid_from=datetime.now(timezone.utc),
        poll_execution_id=poll_execution_id,
    )
    db.add(version)
    db.flush()
    return version


def make_poll_execution(db, status="success"):
    pe = PollExecution(
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
        status=status,
    )
    db.add(pe)
    db.flush()
    return pe


def make_customer(db, first_name="John", last_name="Doe", email="john@test.com", phone=None):
    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
    )
    db.add(customer)
    db.flush()
    return customer


def make_resource(db, name="Boat", type_name="vehicle", quantity_available=5):
    resource = Resource(
        name=name,
        type=type_name,
        quantity_available=quantity_available,
    )
    db.add(resource)
    db.flush()
    return resource


def make_cost(db, tour_id, ticket_type="adult", price=50.00):
    cost = Cost(
        tour_id=tour_id,
        ticket_type=ticket_type,
        price=price,
        valid_from=datetime.now(timezone.utc),
        valid_to=datetime(2027, 12, 31, tzinfo=timezone.utc),
    )
    db.add(cost)
    db.flush()
    return cost


def make_schedule(db, booking_version_id, guide_id, resource_id=None):
    schedule = Schedule(
        booking_version_id=booking_version_id,
        guide_id=guide_id,
        resource_id=resource_id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )
    db.add(schedule)
    db.flush()
    return schedule


def make_survey(db, customer_id, guide_id, booking_version_id, rating=5, comment=None):
    survey = Survey(
        customer_id=customer_id,
        guide_id=guide_id,
        booking_version_id=booking_version_id,
        rating=rating,
        comment=comment,
    )
    db.add(survey)
    db.flush()
    return survey


def make_user(db, username="admin", email="admin@test.com", role="admin"):
    user = User(
        username=username,
        email=email,
        password_hash="hashed_password",
        full_name="Admin User",
        role=role,
    )
    db.add(user)
    db.flush()
    return user
