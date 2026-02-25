"""Unit tests for sync scheduler module."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from unittest.mock import MagicMock, patch

from app.adapters.clorian_mock import ClorianMockClient
from app.jobs.sync_scheduler import (
    get_sync_service,
    init_sync_service,
    run_sync_job,
)
from app.models.sync_log import SyncLog


def test_init_and_get_sync_service():
    client = ClorianMockClient()
    init_sync_service(client)
    service = get_sync_service()
    assert service is not None


def test_run_sync_job_executes_sync(db):
    from unittest.mock import patch, MagicMock

    client = ClorianMockClient()
    client.clear()
    init_sync_service(client)

    mock_session = MagicMock()
    with patch("app.jobs.sync_scheduler.SessionLocal", return_value=mock_session):
        run_sync_job()

    service = get_sync_service()
    assert service is not None
    mock_session.close.assert_called_once()


def test_run_sync_job_skips_when_service_not_initialized(db):
    from app.jobs import sync_scheduler

    original = sync_scheduler._sync_service
    sync_scheduler._sync_service = None
    try:
        run_sync_job()
        logs = db.query(SyncLog).all()
        assert len(logs) == 0
    finally:
        sync_scheduler._sync_service = original


def test_run_sync_job_skips_when_lock_held(db):
    from app.jobs.sync_scheduler import _lock

    client = ClorianMockClient()
    client.clear()
    init_sync_service(client)

    _lock.acquire()
    try:
        run_sync_job()
        logs = db.query(SyncLog).all()
        assert len(logs) == 0
    finally:
        _lock.release()
