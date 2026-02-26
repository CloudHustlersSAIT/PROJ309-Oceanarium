import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.audit_log import TourAssignmentLog
from ..models.booking_version import BookingVersion
from ..models.guide import Guide
from ..models.schedule import Schedule
from ..models.tour import Tour

logger = logging.getLogger(__name__)


def _schedule_window(bv: BookingVersion) -> tuple:
    """Derive (start_datetime, end_datetime) from a BookingVersion."""
    return (
        datetime.combine(bv.start_date, bv.start_time or datetime.min.time()),
        datetime.combine(bv.start_date, bv.end_time or datetime.max.time()),
    )


def assign_guide_to_booking(
    booking_version: BookingVersion, guide: Guide, db: Session
) -> Schedule:
    """Create a Schedule record linking a booking version to a guide."""
    start_dt, end_dt = _schedule_window(booking_version)
    schedule = Schedule(
        booking_version_id=booking_version.id,
        guide_id=guide.id,
        start_date=start_dt,
        end_date=end_dt,
    )
    db.add(schedule)

    booking_version.status = "assigned"
    db.flush()

    booking = booking_version.booking
    if booking and booking.tour_id:
        _log_assignment(db, booking.tour_id, guide, action="assigned", assignment_type="auto")

    logger.info(
        "BookingVersion %s assigned to guide %s (%s %s)",
        booking_version.id, guide.id, guide.first_name, guide.last_name,
    )
    return schedule


def manual_assign(
    booking_version: BookingVersion,
    guide: Guide,
    db: Session,
    assigned_by: str,
) -> Schedule:
    """Manually assign a guide to a booking version, bypassing suitability checks."""
    existing = (
        db.query(Schedule)
        .filter(Schedule.booking_version_id == booking_version.id)
        .first()
    )
    if existing:
        old_guide = db.get(Guide, existing.guide_id)
        if old_guide and booking_version.booking and booking_version.booking.tour_id:
            _log_assignment(
                db, booking_version.booking.tour_id, old_guide,
                action="released", assignment_type="manual", assigned_by=assigned_by,
            )
        db.delete(existing)
        db.flush()

    start_dt, end_dt = _schedule_window(booking_version)
    schedule = Schedule(
        booking_version_id=booking_version.id,
        guide_id=guide.id,
        start_date=start_dt,
        end_date=end_dt,
    )
    db.add(schedule)

    booking_version.status = "assigned"
    db.flush()

    if booking_version.booking and booking_version.booking.tour_id:
        _log_assignment(
            db, booking_version.booking.tour_id, guide,
            action="assigned", assignment_type="manual", assigned_by=assigned_by,
        )

    logger.info(
        "BookingVersion %s manually assigned to guide %s by %s",
        booking_version.id, guide.id, assigned_by,
    )
    return schedule


def release_guide_from_schedule(schedule: Schedule, db: Session, reason: str = "released") -> None:
    """Remove a guide from a schedule."""
    if schedule.booking_version:
        schedule.booking_version.status = "unassigned"
        if schedule.booking_version.booking:
            tour_id = schedule.booking_version.booking.tour_id
            if tour_id:
                guide = db.get(Guide, schedule.guide_id)
                _log_assignment(db, tour_id, guide, action=reason, assignment_type="auto")

    db.delete(schedule)
    db.flush()


def _log_assignment(
    db: Session,
    tour_id: int,
    guide: Optional[Guide],
    action: str,
    assignment_type: str,
    assigned_by: Optional[str] = None,
) -> TourAssignmentLog:
    log = TourAssignmentLog(
        tour_id=tour_id,
        guide_id=guide.id if guide else None,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=assigned_by,
        assignment_type=assignment_type,
        action=action,
    )
    db.add(log)
    db.flush()
    return log
