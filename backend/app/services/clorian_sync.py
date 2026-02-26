import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..adapters.clorian_client import ClorianBooking, ClorianClientBase
from ..models.booking import Booking
from ..models.booking_version import BookingVersion
from ..models.customer import Customer
from ..models.poll_execution import PollExecution
from ..models.schedule import Schedule
from ..models.sync_log import SyncLog
from ..models.tour import Tour

logger = logging.getLogger(__name__)


def _compute_hash(
    booking_id: int,
    status: str,
    adult_tickets: int,
    child_tickets: int,
    start_date,
    start_time=None,
    end_time=None,
) -> str:
    raw = (
        f"{booking_id}|{status}|{adult_tickets}|{child_tickets}"
        f"|{start_date}|{start_time}|{end_time}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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

            assigned = assign_unassigned_bookings(db)

            logger.info(
                "Sync completed: new=%d changed=%d cancelled=%d auto_assigned=%d",
                new_count, changed_count, cancelled_count, assigned,
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
            else:
                if cb.requested_language_code and existing.requested_language_code != cb.requested_language_code:
                    existing.requested_language_code = cb.requested_language_code
                if self._has_changes(existing, cb):
                    changed_count += self._update_booking(db, existing, cb, poll_id)

        for clorian_id, booking in local_map.items():
            if clorian_id not in clorian_ids:
                cancelled_count += self._cancel_booking(db, booking, poll_id)

        db.commit()
        return new_count, changed_count, cancelled_count

    def _create_booking(self, db: Session, cb: ClorianBooking, poll_id: int) -> int:
        customer_id = _resolve_customer(db, cb)
        tour_id = _resolve_tour(db, cb)

        booking = Booking(
            clorian_booking_id=cb.clorian_booking_id,
            customer_id=customer_id,
            tour_id=tour_id,
            requested_language_code=cb.requested_language_code,
        )
        db.add(booking)
        db.flush()

        version_hash = _compute_hash(
            booking.booking_id,
            "unassigned",
            cb.adult_tickets,
            cb.child_tickets,
            cb.date,
            cb.start_time,
            cb.end_time,
        )
        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="unassigned",
            adult_tickets=cb.adult_tickets,
            child_tickets=cb.child_tickets,
            start_date=cb.date,
            start_time=cb.start_time,
            end_time=cb.end_time,
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

        version_hash = _compute_hash(
            booking.booking_id,
            "unassigned",
            cb.adult_tickets,
            cb.child_tickets,
            cb.date,
            cb.start_time,
            cb.end_time,
        )

        if lv and lv.hash == version_hash:
            return 0

        customer_id = _resolve_customer(db, cb)
        tour_id = _resolve_tour(db, cb)
        if customer_id and booking.customer_id != customer_id:
            booking.customer_id = customer_id
        if tour_id and booking.tour_id != tour_id:
            booking.tour_id = tour_id
        if cb.requested_language_code and booking.requested_language_code != cb.requested_language_code:
            booking.requested_language_code = cb.requested_language_code

        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="unassigned",
            adult_tickets=cb.adult_tickets,
            child_tickets=cb.child_tickets,
            start_date=cb.date,
            start_time=cb.start_time,
            end_time=cb.end_time,
            valid_from=datetime.now(timezone.utc),
            poll_execution_id=poll_id,
        )
        db.add(version)
        db.flush()

        if lv:
            for old_schedule in lv.schedules:
                db.delete(old_schedule)
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
            lv.start_time if lv else None,
            lv.end_time if lv else None,
        )

        version = BookingVersion(
            booking_id=booking.booking_id,
            hash=version_hash,
            status="cancelled",
            adult_tickets=lv.adult_tickets if lv else 0,
            child_tickets=lv.child_tickets if lv else 0,
            start_date=lv.start_date if lv else datetime.now(timezone.utc).date(),
            start_time=lv.start_time if lv else None,
            end_time=lv.end_time if lv else None,
            valid_from=datetime.now(timezone.utc),
            poll_execution_id=poll_id,
        )
        db.add(version)
        db.flush()

        if lv:
            for old_schedule in lv.schedules:
                db.delete(old_schedule)
            db.flush()

        return 1

    @staticmethod
    def _has_changes(booking: Booking, cb: ClorianBooking) -> bool:
        lv = booking.latest_version
        if lv is None:
            return True
        return (
            lv.start_date != cb.date
            or lv.adult_tickets != cb.adult_tickets
            or lv.child_tickets != cb.child_tickets
            or lv.start_time != cb.start_time
            or lv.end_time != cb.end_time
        )


def _resolve_customer(db: Session, cb: ClorianBooking) -> Optional[int]:
    """Find or create a Customer from Clorian booking data."""
    if not cb.customer_email:
        return None
    customer = db.query(Customer).filter(Customer.email == cb.customer_email).first()
    if customer:
        return customer.id
    parts = (cb.customer_name or "").split(None, 1)
    first_name = parts[0] if parts else "Unknown"
    last_name = parts[1] if len(parts) > 1 else ""
    customer = Customer(
        first_name=first_name,
        last_name=last_name,
        email=cb.customer_email,
    )
    db.add(customer)
    db.flush()
    return customer.id


def _resolve_tour(db: Session, cb: ClorianBooking) -> Optional[int]:
    """Find or create a Tour from Clorian booking data."""
    if not cb.tour_name:
        return None
    tour = db.query(Tour).filter(Tour.name == cb.tour_name).first()
    if tour:
        return tour.id
    tour = Tour(name=cb.tour_name)
    db.add(tour)
    db.flush()
    return tour.id


def assign_unassigned_bookings(db: Session) -> int:
    """Re-evaluate all pending bookings without a schedule.

    Called when guides are created/updated/given availability.
    Returns the number of newly assigned bookings.
    """
    from sqlalchemy import func

    from ..services.assignment import assign_guide_to_booking
    from ..services.guide_matcher import find_eligible_guides

    latest_version_ids = (
        db.query(func.max(BookingVersion.id))
        .group_by(BookingVersion.booking_id)
        .scalar_subquery()
    )
    latest_versions = (
        db.query(BookingVersion)
        .filter(
            BookingVersion.id.in_(latest_version_ids),
            BookingVersion.status == "unassigned",
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

        eligible_guides = find_eligible_guides(version, db)
        if not eligible_guides:
            continue

        assign_guide_to_booking(version, eligible_guides[0], db)
        assigned_count += 1

    if assigned_count > 0:
        db.commit()
        logger.info("Reassignment pass: %d bookings newly assigned", assigned_count)

    return assigned_count
