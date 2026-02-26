import logging
from datetime import date, datetime
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.availability import AvailabilityException, AvailabilitySlot
from ..models.booking_version import BookingVersion
from ..models.guide import Guide
from ..models.schedule import Schedule
from ..models.tour import Tour

logger = logging.getLogger(__name__)


def find_eligible_guides(
    booking_version: BookingVersion, db: Session
) -> List[Guide]:
    """Find all guides eligible for a booking version, sorted by fewest assignments that day.

    A guide is eligible only if ALL rules pass (AND logic):
      Rule 1: Available (slot covers the day, no blocking exception, no overlap, active)
      Rule 2: Can lead this tour type (via guide_tour_types)
    """
    active_guides = db.query(Guide).filter(Guide.is_active.is_(True)).all()

    tour_id = None
    if booking_version.booking:
        tour_id = booking_version.booking.tour_id

    eligible: List[Guide] = []
    for guide in active_guides:
        if not _check_availability(guide, booking_version, db):
            continue
        if tour_id and not _check_tour_type(guide, tour_id):
            continue
        eligible.append(guide)

    schedule_counts = _batch_count_schedules_on_date(
        [g.id for g in eligible], booking_version.start_date, db
    )
    eligible.sort(key=lambda g: schedule_counts.get(g.id, 0))

    return eligible


def is_guide_available_on_date(
    guide: Guide, target_date: date, db: Session
) -> bool:
    """Check whether *guide* can work on *target_date*.

    Rules (all must pass):
      1. Guide has an availability pattern with a slot covering the weekday.
      2. No blocking exception exists for that date.
      3. No overlapping schedule already exists for the guide on that date.
    """
    pattern = guide.availability_pattern
    if pattern is None:
        return False

    if not any(slot.day_of_week == target_date.weekday() for slot in pattern.slots):
        return False

    has_blocking = (
        db.query(AvailabilityException)
        .filter(
            AvailabilityException.pattern_id == pattern.id,
            AvailabilityException.date == target_date,
            AvailabilityException.type == "blocked",
        )
        .first()
    )
    if has_blocking:
        return False

    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    overlapping = (
        db.query(Schedule)
        .filter(
            Schedule.guide_id == guide.id,
            Schedule.start_date < end_dt,
            Schedule.end_date > start_dt,
        )
        .first()
    )
    if overlapping:
        return False

    return True


def _check_availability(
    guide: Guide, booking_version: BookingVersion, db: Session
) -> bool:
    return is_guide_available_on_date(guide, booking_version.start_date, db)


def _check_tour_type(guide: Guide, tour_id: int) -> bool:
    for tour in guide.tour_types:
        if tour.id == tour_id:
            return True
    return False


def _batch_count_schedules_on_date(
    guide_ids: List[int], schedule_date: date, db: Session
) -> Dict[int, int]:
    if not guide_ids:
        return {}
    start_dt = datetime.combine(schedule_date, datetime.min.time())
    end_dt = datetime.combine(schedule_date, datetime.max.time())
    rows = (
        db.query(Schedule.guide_id, func.count(Schedule.id))
        .filter(
            Schedule.guide_id.in_(guide_ids),
            Schedule.start_date >= start_dt,
            Schedule.start_date < end_dt,
        )
        .group_by(Schedule.guide_id)
        .all()
    )
    return {guide_id: count for guide_id, count in rows}
