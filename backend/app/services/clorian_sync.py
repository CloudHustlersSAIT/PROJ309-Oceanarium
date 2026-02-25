import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..adapters.clorian_client import ClorianBooking, ClorianClientBase
from ..models.booking import Booking
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

        active_bookings = (
            db.query(Booking)
            .filter(Booking.status != "cancelled")
            .all()
        )
        local_map = {b.clorian_booking_id: b for b in active_bookings}

        for cb in clorian_bookings:
            existing = local_map.get(cb.clorian_booking_id)

            if existing is None:
                new_count += self._create_booking(db, cb)
            elif self._has_changes(existing, cb):
                changed_count += self._update_booking(db, existing, cb)

        for clorian_id, booking in local_map.items():
            if clorian_id not in clorian_ids:
                cancelled_count += self._cancel_booking(db, booking)

        db.commit()
        return new_count, changed_count, cancelled_count

    def _create_booking(self, db: Session, cb: ClorianBooking) -> int:
        booking = Booking(
            clorian_booking_id=cb.clorian_booking_id,
            date=cb.date,
            start_time=cb.start_time,
            end_time=cb.end_time,
            required_expertise=cb.required_expertise,
            required_category=cb.required_category,
            requested_language_code=cb.requested_language_code,
            status="pending",
        )
        db.add(booking)
        db.flush()

        self._try_assign(db, booking)
        return 1

    def _update_booking(self, db: Session, booking: Booking, cb: ClorianBooking) -> int:
        if booking.tour_id is not None:
            tour = db.get(Tour, booking.tour_id)
            if tour and tour.assigned_guide_id is not None:
                release_guide(tour, db, reason="released")
            if tour:
                tour.status = "cancelled"
            booking.tour_id = None

        booking.date = cb.date
        booking.start_time = cb.start_time
        booking.end_time = cb.end_time
        booking.required_expertise = cb.required_expertise
        booking.required_category = cb.required_category
        booking.requested_language_code = cb.requested_language_code
        booking.status = "pending"
        db.flush()

        self._try_assign(db, booking)
        return 1

    def _cancel_booking(self, db: Session, booking: Booking) -> int:
        if booking.tour_id is not None:
            tour = db.get(Tour, booking.tour_id)
            if tour and tour.assigned_guide_id is not None:
                release_guide(tour, db, reason="released")
            if tour:
                tour.status = "cancelled"

        booking.status = "cancelled"
        booking.tour_id = None
        return 1

    def _try_assign(self, db: Session, booking: Booking) -> None:
        """Create a temporary Tour object from booking data to run guide matching.

        If a guide is found, persist the tour and link it to the booking.
        If no guide is found, the booking stays as 'pending' without a tour.
        """
        candidate_tour = Tour(
            clorian_booking_id=booking.clorian_booking_id,
            date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            required_expertise=booking.required_expertise,
            required_category=booking.required_category,
            requested_language_code=booking.requested_language_code,
            status="pending",
        )
        db.add(candidate_tour)
        db.flush()

        guide = assign_guide_to_tour(candidate_tour, db)

        if guide is not None:
            booking.tour_id = candidate_tour.id
            booking.status = "assigned"
        else:
            db.delete(candidate_tour)
            booking.status = "pending"

        db.flush()

    @staticmethod
    def _has_changes(booking: Booking, cb: ClorianBooking) -> bool:
        return (
            booking.date != cb.date
            or booking.start_time != cb.start_time
            or booking.end_time != cb.end_time
            or booking.required_expertise != cb.required_expertise
            or booking.required_category != cb.required_category
            or booking.requested_language_code != cb.requested_language_code
        )


def assign_unassigned_bookings(db: Session) -> int:
    """Re-evaluate all pending bookings without a tour.

    Called when guides are created/updated/given availability.
    Returns the number of newly assigned bookings.
    """
    unassigned = (
        db.query(Booking)
        .filter(Booking.status == "pending", Booking.tour_id.is_(None))
        .all()
    )

    assigned_count = 0
    sync_service = ClorianSyncService.__new__(ClorianSyncService)

    for booking in unassigned:
        sync_service._try_assign(db, booking)
        if booking.tour_id is not None:
            assigned_count += 1

    if assigned_count > 0:
        db.commit()
        logger.info("Reassignment pass: %d bookings newly assigned", assigned_count)

    return assigned_count
