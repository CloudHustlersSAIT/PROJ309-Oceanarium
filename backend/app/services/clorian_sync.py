import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..adapters.clorian_client import ClorianBooking, ClorianClientBase
from ..models.booking import Booking
from ..models.booking_version import BookingVersion
from ..models.poll_execution import PollExecution
from ..models.schedule import Schedule
from ..models.sync_log import SyncLog

logger = logging.getLogger(__name__)


def _compute_hash(
    booking_id: int,
    status: str,
    adult_tickets: int,
    child_tickets: int,
    start_date,
) -> str:
    raw = f"{booking_id}|{status}|{adult_tickets}|{child_tickets}|{start_date}"
    return hashlib.md5(raw.encode()).hexdigest()


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

        poll = PollExecution(
            window_start=datetime.now(timezone.utc),
            window_end=datetime.now(timezone.utc),
            status="running",
        )
        db.add(poll)
        db.flush()

        try:
            clorian_bookings = self._client.fetch_bookings()
            new_count, changed_count, cancelled_count = self._process_bookings(
                db, clorian_bookings, poll.id
            )

            sync_log.new_count = new_count
            sync_log.changed_count = changed_count
            sync_log.cancelled_count = cancelled_count
            sync_log.status = "success"
            sync_log.finished_at = datetime.now(timezone.utc)

            poll.status = "success"
            poll.window_end = datetime.now(timezone.utc)
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
            poll.status = "failed"
            poll.window_end = datetime.now(timezone.utc)
            db.commit()

            logger.error("Sync failed (attempt %d): %s", self._consecutive_failures, e)

            if self._consecutive_failures >= 3:
                logger.critical(
                    "Clorian sync has failed %d consecutive times — admin notification required",
                    self._consecutive_failures,
                )

            return sync_log

    def _process_bookings(
        self, db: Session, clorian_bookings: list[ClorianBooking], poll_id: int
    ) -> tuple[int, int, int]:
        new_count = 0
        changed_count = 0
        cancelled_count = 0

        clorian_ids = {b.clorian_booking_id for b in clorian_bookings}

        active_bookings = db.query(Booking).all()
        active_with_version = []
        for b in active_bookings:
            lv = b.latest_version
            if lv and lv.status != "cancelled":
                active_with_version.append(b)
            elif not lv:
                active_with_version.append(b)

        local_map = {b.clorian_booking_id: b for b in active_with_version}

        for cb in clorian_bookings:
            existing = local_map.get(cb.clorian_booking_id)

            if existing is None:
                new_count += self._create_booking(db, cb, poll_id)
            elif self._has_changes(existing, cb):
                changed_count += self._update_booking(db, existing, cb, poll_id)

        for clorian_id, booking in local_map.items():
            if clorian_id not in clorian_ids:
                cancelled_count += self._cancel_booking(db, booking, poll_id)

        db.commit()
        return new_count, changed_count, cancelled_count

    def _create_booking(self, db: Session, cb: ClorianBooking, poll_id: int) -> int:
        booking = Booking(
            clorian_booking_id=cb.clorian_booking_id,
        )
        db.add(booking)
        db.flush()

        version_hash = _compute_hash(
            booking.booking_id, "pending", 0, 0, cb.date,
        )
        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="pending",
            adult_tickets=0,
            child_tickets=0,
            start_date=cb.date,
            valid_from=datetime.now(timezone.utc),
            poll_execution_id=poll_id,
        )
        db.add(version)
        db.flush()

        return 1

    def _update_booking(
        self, db: Session, booking: Booking, cb: ClorianBooking, poll_id: int
    ) -> int:
        lv = booking.latest_version
        status = lv.status if lv else "pending"

        version_hash = _compute_hash(
            booking.booking_id, status, 0, 0, cb.date,
        )

        if lv and lv.hash == version_hash:
            return 0

        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="pending",
            adult_tickets=lv.adult_tickets if lv else 0,
            child_tickets=lv.child_tickets if lv else 0,
            start_date=cb.date,
            valid_from=datetime.now(timezone.utc),
            poll_execution_id=poll_id,
        )
        db.add(version)
        db.flush()

        return 1

    def _cancel_booking(self, db: Session, booking: Booking, poll_id: int) -> int:
        lv = booking.latest_version
        if lv and lv.status == "cancelled":
            return 0

        version_hash = _compute_hash(
            booking.booking_id,
            "cancelled",
            lv.adult_tickets if lv else 0,
            lv.child_tickets if lv else 0,
            lv.start_date if lv else "1970-01-01",
        )

        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="cancelled",
            adult_tickets=lv.adult_tickets if lv else 0,
            child_tickets=lv.child_tickets if lv else 0,
            start_date=lv.start_date if lv else datetime.now(timezone.utc).date(),
            valid_from=datetime.now(timezone.utc),
            poll_execution_id=poll_id,
        )
        db.add(version)
        db.flush()

        return 1

    @staticmethod
    def _has_changes(booking: Booking, cb: ClorianBooking) -> bool:
        lv = booking.latest_version
        if lv is None:
            return True
        return lv.start_date != cb.date


def assign_unassigned_bookings(db: Session) -> int:
    """Re-evaluate all pending bookings without a schedule.

    Called when guides are created/updated/given availability.
    Returns the number of newly assigned bookings.
    """
    from ..models.booking_version import BookingVersion
    from sqlalchemy import func

    latest_version_ids = (
        db.query(func.max(BookingVersion.id))
        .group_by(BookingVersion.booking_id)
        .scalar_subquery()
    )
    latest_versions = (
        db.query(BookingVersion)
        .filter(
            BookingVersion.id.in_(latest_version_ids),
            BookingVersion.status == "pending",
        )
        .all()
    )

    assigned_count = 0
    for version in latest_versions:
        existing_schedule = (
            db.query(Schedule)
            .filter(Schedule.booking_version_id == version.id)
            .first()
        )
        if existing_schedule:
            continue

        assigned_count += 1

    if assigned_count > 0:
        db.commit()
        logger.info("Reassignment pass: %d bookings newly assigned", assigned_count)

    return assigned_count
