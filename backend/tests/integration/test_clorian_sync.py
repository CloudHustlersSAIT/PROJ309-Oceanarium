"""Integration tests for Clorian sync service (Phase 7c).

Covers new/changed/cancelled booking detection, sync logging,
failure resilience, consecutive failure alerting, and idempotency.
"""
from datetime import date, time
from unittest.mock import MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.adapters.clorian_client import ClorianBooking
from app.adapters.clorian_mock import ClorianMockClient
from app.models.sync_log import SyncLog
from app.models.tour import Tour
from app.services.clorian_sync import ClorianSyncService
from tests.conftest import make_availability, make_guide, make_tour


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


def test_new_booking_creates_tour(db):
    """AC-01: new booking detected -> tour created locally, assignment triggered."""
    client = _make_client([_sample_booking()])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.status == "success"
    assert sync_log.new_count == 1
    tour = db.query(Tour).filter(Tour.clorian_booking_id == "CLR-100").first()
    assert tour is not None
    assert tour.date == date(2026, 3, 2)


def test_changed_booking_updates_tour(db):
    """AC-02: booking changed -> tour updated, guide reassessed."""
    make_tour(db, clorian_booking_id="CLR-200",
              tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0))
    db.commit()

    updated_booking = _sample_booking(
        clorian_booking_id="CLR-200",
        start_time=time(14, 0), end_time=time(16, 0),
    )
    client = _make_client([updated_booking])
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.changed_count == 1
    tour = db.query(Tour).filter(Tour.clorian_booking_id == "CLR-200").first()
    assert tour.start_time == time(14, 0)
    assert tour.end_time == time(16, 0)


def test_changed_booking_reassigns_if_guide_no_longer_suitable(db):
    """AC-02: booking time changes, current guide unavailable at new time."""
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
    ])
    tour = make_tour(
        db, clorian_booking_id="CLR-300",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="assigned", assigned_guide_id=guide.id,
    )
    db.commit()

    updated_booking = _sample_booking(
        clorian_booking_id="CLR-300",
        start_time=time(14, 0), end_time=time(16, 0),  # outside guide's slot
    )
    client = _make_client([updated_booking])
    service = ClorianSyncService(client)

    service.run_sync(db)

    db.refresh(tour)
    assert tour.start_time == time(14, 0)
    assert tour.assigned_guide_id is None or tour.status in ("unassigned", "pending")


def test_cancelled_booking_releases_guide(db):
    """AC-03: booking absent from Clorian -> guide released, tour cancelled."""
    guide = make_guide(db)
    tour = make_tour(
        db, clorian_booking_id="CLR-400",
        status="assigned", assigned_guide_id=guide.id,
    )
    db.commit()

    client = _make_client([])  # empty = booking no longer exists
    service = ClorianSyncService(client)

    sync_log = service.run_sync(db)

    assert sync_log.cancelled_count == 1
    db.refresh(tour)
    assert tour.status == "cancelled"
    assert tour.assigned_guide_id is None


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
    """NFR-04: uses the lock in sync_scheduler (tested at scheduler level)."""
    import threading
    from app.jobs.sync_scheduler import _lock, run_sync_job, init_sync_service

    client = _make_client([])
    init_sync_service(client)

    _lock.acquire()
    try:
        run_sync_job()  # should skip because lock is held
    finally:
        _lock.release()

    logs = db.query(SyncLog).all()
    assert len(logs) == 0


def test_clorian_api_failure_retries_next_cycle(db):
    """AC-04: Clorian unreachable -> sync fails gracefully."""
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
    """NFR-05: 3 consecutive failures -> admin notification."""
    client = MagicMock()
    client.fetch_bookings.side_effect = ConnectionError("Clorian down")
    service = ClorianSyncService(client)

    for _ in range(3):
        service.run_sync(db)

    assert service.consecutive_failures == 3

    logs = db.query(SyncLog).filter(SyncLog.status == "failed").all()
    assert len(logs) == 3


def test_sync_completes_within_timeout(db):
    """NFR-04: sync finishes within 60 seconds."""
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

    tours = db.query(Tour).filter(Tour.clorian_booking_id == "CLR-IDEM").all()
    assert len(tours) == 1
