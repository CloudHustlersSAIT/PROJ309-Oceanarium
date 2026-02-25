import logging
import threading
from typing import Optional

from ..adapters.clorian_client import ClorianClientBase
from ..db import SessionLocal
from ..services.clorian_sync import ClorianSyncService

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_running = False

_sync_service: Optional[ClorianSyncService] = None


def init_sync_service(client: ClorianClientBase) -> None:
    global _sync_service
    _sync_service = ClorianSyncService(client)


def get_sync_service() -> Optional[ClorianSyncService]:
    return _sync_service


def run_sync_job() -> None:
    global _running

    if not _lock.acquire(blocking=False):
        logger.warning("Sync job skipped — previous cycle still running (NFR-04)")
        return

    try:
        _running = True
        logger.info("Starting Clorian sync cycle")

        if _sync_service is None:
            logger.error("Sync service not initialised — skipping")
            return

        db = SessionLocal()
        try:
            _sync_service.run_sync(db)
        finally:
            db.close()
    finally:
        _running = False
        _lock.release()
