import logging
from datetime import date, time
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.availability import AvailabilityException, AvailabilitySlot
from ..models.guide import Guide
from ..models.tour import Tour

logger = logging.getLogger(__name__)


def find_eligible_guides(tour: Tour, db: Session) -> List[Guide]:
    """Find all guides eligible for a tour, sorted by fewest assignments that day.

    A guide is eligible only if ALL three rules pass (AND logic):
      Rule 1: Available (slot covers window, no blocking exception, no overlap, active)
      Rule 2: Has matching expertise (by name or category)
      Rule 3: Speaks the requested language
    """
    active_guides = db.query(Guide).filter(Guide.is_active.is_(True)).all()

    eligible: List[Guide] = []
    for guide in active_guides:
        if not _check_availability(guide, tour, db):
            continue
        if not _check_expertise(guide, tour):
            continue
        if not _check_language(guide, tour):
            continue
        eligible.append(guide)

    tour_counts = _batch_count_tours_on_date(
        [g.id for g in eligible], tour.date, db
    )
    eligible.sort(key=lambda g: tour_counts.get(g.id, 0))

    return eligible


def _check_availability(guide: Guide, tour: Tour, db: Session) -> bool:
    pattern = guide.availability_pattern
    if pattern is None:
        return False

    tour_day = tour.date.weekday()  # 0=Monday ... 6=Sunday

    has_covering_slot = any(
        slot.day_of_week == tour_day
        and slot.start_time <= tour.start_time
        and slot.end_time >= tour.end_time
        for slot in pattern.slots
    )
    if not has_covering_slot:
        return False

    has_blocking = (
        db.query(AvailabilityException)
        .filter(
            AvailabilityException.pattern_id == pattern.id,
            AvailabilityException.date == tour.date,
            AvailabilityException.type == "blocked",
        )
        .first()
    )
    if has_blocking:
        return False

    overlapping = (
        db.query(Tour)
        .filter(
            Tour.assigned_guide_id == guide.id,
            Tour.date == tour.date,
            Tour.id != tour.id,
            Tour.status != "cancelled",
            Tour.start_time < tour.end_time,
            Tour.end_time > tour.start_time,
        )
        .first()
    )
    if overlapping:
        return False

    return True


def _check_expertise(guide: Guide, tour: Tour) -> bool:
    if not tour.required_expertise and not tour.required_category:
        return True

    for exp in guide.expertises:
        if tour.required_expertise and exp.name == tour.required_expertise:
            return True
        if tour.required_category and exp.category == tour.required_category:
            return True

    return False


def _check_language(guide: Guide, tour: Tour) -> bool:
    if not tour.requested_language_code:
        return True

    for lang in guide.languages:
        if lang.code == tour.requested_language_code:
            return True

    return False


def _batch_count_tours_on_date(
    guide_ids: List[int], tour_date: date, db: Session
) -> Dict[int, int]:
    if not guide_ids:
        return {}
    rows = (
        db.query(Tour.assigned_guide_id, func.count(Tour.id))
        .filter(
            Tour.assigned_guide_id.in_(guide_ids),
            Tour.date == tour_date,
            Tour.status != "cancelled",
        )
        .group_by(Tour.assigned_guide_id)
        .all()
    )
    return {guide_id: count for guide_id, count in rows}
