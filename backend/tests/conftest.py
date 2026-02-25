import os
from datetime import date, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///test_unused.db")

from app.db import Base, get_db
from app.models.availability import (
    AvailabilityException,
    AvailabilityPattern,
    AvailabilitySlot,
)
from app.models.booking import Booking
from app.models.guide import Expertise, Guide, Language
from app.models.issue import Issue
from app.models.tour import Tour

TEST_DB_URL = "sqlite:///test_runner.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


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
    name="Test Guide",
    email=None,
    is_active=True,
    language_codes=None,
    expertise_names=None,
    expertise_categories=None,
):
    if email is None:
        import uuid
        email = f"{uuid.uuid4().hex[:8]}@test.com"
    if language_codes is None:
        language_codes = ["en"]
    if expertise_names is None:
        expertise_names = ["Sharks"]
    if expertise_categories is None:
        expertise_categories = ["Marine Biology"] * len(expertise_names)

    guide = Guide(name=name, email=email, is_active=is_active)
    db.add(guide)
    db.flush()

    for code in language_codes:
        lang = db.query(Language).filter(Language.code == code).first()
        if not lang:
            lang = Language(code=code, name=code)
            db.add(lang)
            db.flush()
        guide.languages.append(lang)

    for exp_name, cat in zip(expertise_names, expertise_categories):
        exp = db.query(Expertise).filter(Expertise.name == exp_name).first()
        if not exp:
            exp = Expertise(name=exp_name, category=cat)
            db.add(exp)
            db.flush()
        guide.expertises.append(exp)

    db.flush()
    return guide


def make_availability(
    db,
    guide,
    timezone="UTC",
    slots=None,
    exceptions=None,
):
    pattern = AvailabilityPattern(guide_id=guide.id, timezone=timezone)
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
    clorian_booking_id=None,
    tour_date=None,
    start_time=None,
    end_time=None,
    required_expertise="Sharks",
    required_category="Marine Biology",
    requested_language_code="en",
    status="pending",
    assigned_guide_id=None,
):
    if clorian_booking_id is None:
        import uuid
        clorian_booking_id = f"CLR-{uuid.uuid4().hex[:6]}"
    if tour_date is None:
        tour_date = date(2026, 3, 2)  # Monday
    if start_time is None:
        start_time = time(9, 0)
    if end_time is None:
        end_time = time(11, 0)

    tour = Tour(
        clorian_booking_id=clorian_booking_id,
        date=tour_date,
        start_time=start_time,
        end_time=end_time,
        required_expertise=required_expertise,
        required_category=required_category,
        requested_language_code=requested_language_code,
        status=status,
        assigned_guide_id=assigned_guide_id,
    )
    db.add(tour)
    db.flush()
    return tour


def make_booking(
    db,
    clorian_booking_id=None,
    booking_date=None,
    start_time=None,
    end_time=None,
    required_expertise="Sharks",
    required_category="Marine Biology",
    requested_language_code="en",
    status="pending",
    tour_id=None,
):
    if clorian_booking_id is None:
        import uuid
        clorian_booking_id = f"CLR-{uuid.uuid4().hex[:6]}"
    if booking_date is None:
        booking_date = date(2026, 3, 2)
    if start_time is None:
        start_time = time(9, 0)
    if end_time is None:
        end_time = time(11, 0)

    booking = Booking(
        clorian_booking_id=clorian_booking_id,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        required_expertise=required_expertise,
        required_category=required_category,
        requested_language_code=requested_language_code,
        status=status,
        tour_id=tour_id,
    )
    db.add(booking)
    db.flush()
    return booking
