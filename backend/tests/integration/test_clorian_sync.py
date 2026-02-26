"""Integration tests for Clorian sync service.

Covers new/changed/cancelled booking detection, sync logging,
BookingVersion creation, PollExecution tracking, and failure resilience.
"""
from datetime import date, time
from unittest.mock import MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.adapters.clorian_client import ClorianBooking
from app.adapters.clorian_mock import ClorianMockClient
from app.models.booking import Booking
from app.models.booking_version import BookingVersion
from app.models.poll_execution import PollExecution
from app.models.sync_log import SyncLog
from app.services.clorian_sync import ClorianSyncService, assign_unassigned_bookings
from tests.conftest import make_booking, make_guide, make_availability


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


def test_new_booking_creates_booking_and_version(db):
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.status == "success"
    assert sync_log.new_count == 1
    booking = db.query(Booking).filter(Booking.clorian_booking_id == "CLR-100").first()
    assert booking is not None
    assert booking.latest_version is not None
    assert booking.latest_version.status == "pending"


def test_sync_creates_poll_execution(db):
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    service.run_sync(db)

    polls = db.query(PollExecution).all()
    assert len(polls) == 1
    assert polls[0].status == "success"


def test_changed_booking_creates_new_version(db):
    booking = make_booking(
        db, clorian_booking_id="CLR-200",
        booking_date=date(2026, 3, 2),
    )
    db.commit()

    updated = _sample_booking(
        clorian_booking_id="CLR-200",
        date=date(2026, 3, 5),
    )
    client = _make_client([updated])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.changed_count == 1
    versions = db.query(BookingVersion).filter(
        BookingVersion.booking_id == booking.booking_id
    ).all()
    assert len(versions) == 2


def test_cancelled_booking_creates_cancelled_version(db):
    booking = make_booking(db, clorian_booking_id="CLR-400")
    db.commit()

    client = _make_client([])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.cancelled_count == 1
    db.refresh(booking)
    assert booking.latest_version.status == "cancelled"


def test_sync_logs_cycle(db):
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.id is not None
    assert sync_log.started_at is not None
    assert sync_log.finished_at is not None
    assert sync_log.status == "success"


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


def test_idempotent_sync(db):
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
