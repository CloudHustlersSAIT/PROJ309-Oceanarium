import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..adapters.clorian_client import ClorianBooking, ClorianClientBase
from ..models.audit_log import TourAssignmentLog
from ..models.sync_log import SyncLog
from ..models.tour import Tour
from .assignment import assign_guide_to_tour, release_guide

logger = logging.getLogger(__name__)


class ClorianSyncService:
    def __init__(self, client: ClorianClientBase):
        self._client = client
        self._consecutive_failures = 0

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def run_sync(self, db: Session) -> SyncLog:
        sync_log = SyncLog(
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(sync_log)
        db.commit()

        try:
            clorian_bookings = self._client.fetch_bookings()
            new_count, changed_count, cancelled_count = self._process_bookings(
                db, clorian_bookings
            )

            sync_log.new_count = new_count
            sync_log.changed_count = changed_count
            sync_log.cancelled_count = cancelled_count
            sync_log.status = "success"
            sync_log.finished_at = datetime.now(timezone.utc)
            db.commit()

            self._consecutive_failures = 0

            logger.info(
                "Sync completed: new=%d changed=%d cancelled=%d",
                new_count, changed_count, cancelled_count,
            )
            return sync_log

        except Exception as e:
            self._consecutive_failures += 1
            sync_log.status = "failed"
            sync_log.errors = str(e)
            sync_log.finished_at = datetime.now(timezone.utc)
            db.commit()

            logger.error("Sync failed (attempt %d): %s", self._consecutive_failures, e)

            if self._consecutive_failures >= 3:
                logger.critical(
                    "Clorian sync has failed %d consecutive times — admin notification required",
                    self._consecutive_failures,
                )

            return sync_log

    def _process_bookings(
        self, db: Session, clorian_bookings: list[ClorianBooking]
    ) -> tuple[int, int, int]:
        new_count = 0
        changed_count = 0
        cancelled_count = 0

        clorian_ids = {b.clorian_booking_id for b in clorian_bookings}

        active_tours = (
            db.query(Tour)
            .filter(Tour.status.notin_(["cancelled"]))
            .all()
        )
        local_map = {t.clorian_booking_id: t for t in active_tours}

        for booking in clorian_bookings:
            existing_tour = local_map.get(booking.clorian_booking_id)

            if existing_tour is None:
                new_count += self._create_tour(db, booking)
            elif self._has_changes(existing_tour, booking):
                changed_count += self._update_tour(db, existing_tour, booking)

        for clorian_id, tour in local_map.items():
            if clorian_id not in clorian_ids:
                cancelled_count += self._cancel_tour(db, tour)

        db.commit()
        return new_count, changed_count, cancelled_count

    def _create_tour(self, db: Session, booking: ClorianBooking) -> int:
        tour = Tour(
            clorian_booking_id=booking.clorian_booking_id,
            date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            required_expertise=booking.required_expertise,
            required_category=booking.required_category,
            requested_language_code=booking.requested_language_code,
            status="pending",
        )
        db.add(tour)
        db.flush()
        assign_guide_to_tour(tour, db)
        return 1

    def _update_tour(self, db: Session, tour: Tour, booking: ClorianBooking) -> int:
        if tour.assigned_guide_id is not None:
            release_guide(tour, db, reason="released")

        tour.date = booking.date
        tour.start_time = booking.start_time
        tour.end_time = booking.end_time
        tour.required_expertise = booking.required_expertise
        tour.required_category = booking.required_category
        tour.requested_language_code = booking.requested_language_code
        tour.status = "pending"
        db.flush()

        assign_guide_to_tour(tour, db)
        return 1

    def _cancel_tour(self, db: Session, tour: Tour) -> int:
        if tour.assigned_guide_id is not None:
            release_guide(tour, db, reason="released")
        tour.status = "cancelled"
        return 1

    @staticmethod
    def _has_changes(tour: Tour, booking: ClorianBooking) -> bool:
        return (
            tour.date != booking.date
            or tour.start_time != booking.start_time
            or tour.end_time != booking.end_time
            or tour.required_expertise != booking.required_expertise
            or tour.required_category != booking.required_category
            or tour.requested_language_code != booking.requested_language_code
        )
