"""Integration tests for Clorian sync service.

Covers new/changed/cancelled booking detection, sync logging,
guide assignment via bookings, failure resilience, and idempotency.
"""
from datetime import date, time
from unittest.mock import MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.adapters.clorian_client import ClorianBooking
from app.adapters.clorian_mock import ClorianMockClient
from app.models.booking import Booking
from app.models.sync_log import SyncLog
from app.models.tour import Tour
from app.services.clorian_sync import ClorianSyncService, assign_unassigned_bookings
from tests.conftest import make_availability, make_guide, make_tour, make_booking


def _make_client(bookings=None):
    client = ClorianMockClient()
    client.clear()
    if bookings:
        for b in bookings:
            client.add_booking(b)
    return client


def _sample_booking(**overrides):
    defaults = dict(
        clorian_booking_id="CLR-100",
        date=date(2026, 3, 2),
        start_time=time(9, 0),
        end_time=time(11, 0),
        required_expertise="Sharks",
        required_category="Marine Biology",
        requested_language_code="en",
    )
    defaults.update(overrides)
    return ClorianBooking(**defaults)


def test_new_booking_creates_booking_record(db):
    """New Clorian booking -> Booking created in our DB."""
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.status == "success"
    assert sync_log.new_count == 1
    booking = db.query(Booking).filter(Booking.clorian_booking_id == "CLR-100").first()
    assert booking is not None
    assert booking.date == date(2026, 3, 2)
    assert booking.status == "pending"
    assert booking.tour_id is None


def test_new_booking_with_guide_creates_tour(db):
    """New booking + matching guide -> Tour created and linked."""
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
    ])
    db.commit()

    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.new_count == 1
    booking = db.query(Booking).filter(Booking.clorian_booking_id == "CLR-100").first()
    assert booking.status == "assigned"
    assert booking.tour_id is not None

    tour = db.get(Tour, booking.tour_id)
    assert tour.assigned_guide_id == guide.id
    assert tour.status == "assigned"


def test_changed_booking_updates_booking(db):
    """Booking changed in Clorian -> local booking updated, tour reassessed."""
    booking = make_booking(
        db, clorian_booking_id="CLR-200",
        booking_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
    )
    db.commit()

    updated = _sample_booking(
        clorian_booking_id="CLR-200",
        date=date(2026, 3, 5),
        start_time=time(14, 0), end_time=time(16, 0),
    )
    client = _make_client([updated])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.changed_count == 1
    db.refresh(booking)
    assert booking.date == date(2026, 3, 5)
    assert booking.start_time == time(14, 0)
    assert booking.end_time == time(16, 0)


def test_changed_booking_releases_guide_and_cancels_old_tour(db):
    """When booking changes, old tour is cancelled, guide released, new assignment attempted."""
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
    ])
    tour = make_tour(
        db, clorian_booking_id="CLR-300",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="assigned", assigned_guide_id=guide.id,
    )
    booking = make_booking(
        db, clorian_booking_id="CLR-300",
        booking_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="assigned", tour_id=tour.id,
    )
    db.commit()
    old_tour_id = tour.id

    updated = _sample_booking(
        clorian_booking_id="CLR-300",
        start_time=time(14, 0), end_time=time(16, 0),
    )
    client = _make_client([updated])
    service = ClorianSyncService(client)

    service.run_sync(db)

    db.refresh(booking)
    old_tour = db.get(Tour, old_tour_id)
    assert old_tour.status == "cancelled"
    assert old_tour.assigned_guide_id is None
    assert booking.status == "pending"


def test_cancelled_booking_releases_guide(db):
    """Booking absent from Clorian -> booking cancelled, guide released, tour cancelled."""
    guide = make_guide(db)
    tour = make_tour(
        db, clorian_booking_id="CLR-400",
        status="assigned", assigned_guide_id=guide.id,
    )
    booking = make_booking(
        db, clorian_booking_id="CLR-400",
        status="assigned", tour_id=tour.id,
    )
    db.commit()

    client = _make_client([])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.cancelled_count == 1
    db.refresh(tour)
    assert tour.status == "cancelled"
    assert tour.assigned_guide_id is None

    db.refresh(booking)
    assert booking.status == "cancelled"
    assert booking.tour_id is None


def test_sync_logs_cycle(db):
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.id is not None
    assert sync_log.started_at is not None
    assert sync_log.finished_at is not None
    assert sync_log.status == "success"

    persisted = db.query(SyncLog).filter(SyncLog.id == sync_log.id).first()
    assert persisted is not None


def test_sync_skips_if_previous_running(db):
    import threading
    from app.jobs.sync_scheduler import _lock, run_sync_job, init_sync_service

    client = _make_client([])
    init_sync_service(client)

    _lock.acquire()
    try:
        run_sync_job()
    finally:
        _lock.release()

    logs = db.query(SyncLog).all()
    assert len(logs) == 0


def test_clorian_api_failure_retries_next_cycle(db):
    client = MagicMock()
    client.fetch_bookings.side_effect = ConnectionError("Clorian API unreachable")
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.status == "failed"
    assert "unreachable" in sync_log.errors
    assert service.consecutive_failures == 1

    client.fetch_bookings.side_effect = None
    client.fetch_bookings.return_value = []
    sync_log2 = service.run_sync(db)
    assert sync_log2.status == "success"
    assert service.consecutive_failures == 0


def test_three_consecutive_failures_alerts_admin(db):
    client = MagicMock()
    client.fetch_bookings.side_effect = ConnectionError("Clorian down")
    service = ClorianSyncService(client)

    for _ in range(3):
        service.run_sync(db)

    assert service.consecutive_failures == 3

    logs = db.query(SyncLog).filter(SyncLog.status == "failed").all()
    assert len(logs) == 3


def test_sync_completes_within_timeout(db):
    import time as time_mod

    client = _make_client([
        _sample_booking(clorian_booking_id=f"CLR-PERF-{i}")
        for i in range(50)
    ])
    service = ClorianSyncService(client)

    start = time_mod.time()
    service.run_sync(db)
    elapsed = time_mod.time() - start

    assert elapsed < 60


def test_idempotent_sync(db):
    """Same data synced twice -> no duplicates, no unnecessary changes."""
    booking = _sample_booking(clorian_booking_id="CLR-IDEM")
    client = _make_client([booking])
    service = ClorianSyncService(client)

    log1 = service.run_sync(db)
    assert log1.new_count == 1

    log2 = service.run_sync(db)
    assert log2.new_count == 0
    assert log2.changed_count == 0
    assert log2.cancelled_count == 0

    bookings = db.query(Booking).filter(Booking.clorian_booking_id == "CLR-IDEM").all()
    assert len(bookings) == 1


def test_assign_unassigned_bookings_picks_up_pending(db):
    """When a guide becomes available, pending bookings get assigned."""
    booking = make_booking(
        db, clorian_booking_id="CLR-RETRY",
        booking_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
    )
    db.commit()
    assert booking.tour_id is None
    assert booking.status == "pending"

    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
    ])
    db.commit()

    count = assign_unassigned_bookings(db)

    assert count == 1
    db.refresh(booking)
    assert booking.status == "assigned"
    assert booking.tour_id is not None

    tour = db.get(Tour, booking.tour_id)
    assert tour.assigned_guide_id == guide.id


def test_assign_unassigned_bookings_no_match(db):
    """No guide available -> no bookings assigned, returns 0."""
    make_booking(
        db, clorian_booking_id="CLR-NOPE",
        booking_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
    )
    db.commit()

    count = assign_unassigned_bookings(db)
    assert count == 0
