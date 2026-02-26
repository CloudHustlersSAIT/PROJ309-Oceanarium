import logging
from datetime import date, datetime, time
from typing import Dict, List, Optional

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
      Rule 1: Available (slot covers the tour time window, no blocking exception, no overlap, active)
      Rule 2: Can lead this tour type (via guide_tour_types)
      Rule 3: Speaks the requested language (via guide_languages)
    """
    active_guides = db.query(Guide).filter(Guide.is_active.is_(True)).all()

    tour_id = None
    requested_language = None
    if booking_version.booking:
        tour_id = booking_version.booking.tour_id
        requested_language = booking_version.booking.requested_language_code

    eligible: List[Guide] = []
    for guide in active_guides:
        if not _check_availability(guide, booking_version, db):
            continue
        if tour_id and not _check_tour_type(guide, tour_id):
            continue
        if requested_language and not _check_language(guide, requested_language):
            continue
        eligible.append(guide)

    schedule_counts = _batch_count_schedules_on_date(
        [g.id for g in eligible], booking_version.start_date, db
    )
    eligible.sort(key=lambda g: schedule_counts.get(g.id, 0))

    return eligible


def is_guide_available(
    guide: Guide,
    target_date: date,
    db: Session,
    start_time: Optional[time] = None,
    end_time: Optional[time] = None,
) -> bool:
    """Check whether *guide* can work on *target_date* during the given window.

    Rules (all must pass):
      1. Guide has an availability pattern with a slot covering the weekday
         AND whose time range covers [start_time, end_time].
      2. No blocking exception exists for that date.
      3. No overlapping schedule exists for the guide during the window.
    """
    pattern = guide.availability_pattern
    if pattern is None:
        return False

    matching_slots = [s for s in pattern.slots if s.day_of_week == target_date.weekday()]
    if not matching_slots:
        return False

    if start_time and end_time:
        if not any(s.start_time <= start_time and s.end_time >= end_time for s in matching_slots):
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

    window_start = datetime.combine(target_date, start_time or datetime.min.time())
    window_end = datetime.combine(target_date, end_time or datetime.max.time())
    overlapping = (
        db.query(Schedule)
        .filter(
            Schedule.guide_id == guide.id,
            Schedule.start_date < window_end,
            Schedule.end_date > window_start,
        )
        .first()
    )
    if overlapping:
        return False

    return True


def is_guide_available_on_date(
    guide: Guide, target_date: date, db: Session
) -> bool:
    """Backward-compatible day-level check (used by reschedule endpoint)."""
    return is_guide_available(guide, target_date, db)


def _check_availability(
    guide: Guide, booking_version: BookingVersion, db: Session
) -> bool:
    return is_guide_available(
        guide,
        booking_version.start_date,
        db,
        start_time=booking_version.start_time,
        end_time=booking_version.end_time,
    )


def _check_tour_type(guide: Guide, tour_id: int) -> bool:
    for tour in guide.tour_types:
        if tour.id == tour_id:
            return True
    return False


def _check_language(guide: Guide, language_code: str) -> bool:
    return any(lang.code == language_code for lang in guide.languages)


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
