import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.audit_log import TourAssignmentLog
from ..models.guide import Guide
from ..models.tour import Tour
from .guide_matcher import find_eligible_guides

logger = logging.getLogger(__name__)


def assign_guide_to_tour(tour: Tour, db: Session) -> Optional[Guide]:
    """Automatically assign the best-fit guide to a tour.

    Returns the assigned Guide, or None if no suitable guide was found.
    """
    eligible = find_eligible_guides(tour, db)

    if not eligible:
        tour.status = "unassigned"
        db.flush()
        logger.warning("Tour %s flagged as unassigned — no suitable guide", tour.id)
        _log_assignment(db, tour, guide=None, action="unassigned", assignment_type="auto")
        return None

    chosen = eligible[0]

    tour.assigned_guide_id = chosen.id
    tour.status = "assigned"
    db.flush()

    _log_assignment(db, tour, guide=chosen, action="assigned", assignment_type="auto")
    logger.info("Tour %s auto-assigned to guide %s (%s)", tour.id, chosen.id, chosen.name)
    return chosen


def manual_assign(
    tour: Tour, guide: Guide, db: Session, assigned_by: str
) -> None:
    """Manually assign (or override) a guide to a tour, bypassing suitability checks."""
    if tour.assigned_guide_id is not None and tour.assigned_guide_id != guide.id:
        previous_guide = db.get(Guide, tour.assigned_guide_id)
        _log_assignment(
            db, tour, guide=previous_guide, action="released",
            assignment_type="manual", assigned_by=assigned_by,
        )

    tour.assigned_guide_id = guide.id
    tour.status = "assigned"
    db.flush()

    _log_assignment(
        db, tour, guide=guide, action="assigned",
        assignment_type="manual", assigned_by=assigned_by,
    )
    logger.info(
        "Tour %s manually assigned to guide %s by %s",
        tour.id, guide.id, assigned_by,
    )


def release_guide(tour: Tour, db: Session, reason: str = "released") -> None:
    """Release the currently assigned guide from a tour."""
    if tour.assigned_guide_id is None:
        return

    guide = db.get(Guide, tour.assigned_guide_id)
    _log_assignment(db, tour, guide=guide, action=reason, assignment_type="auto")

    tour.assigned_guide_id = None
    if tour.status != "cancelled":
        tour.status = "pending"
    db.flush()


def _log_assignment(
    db: Session,
    tour: Tour,
    guide: Optional[Guide],
    action: str,
    assignment_type: str,
    assigned_by: Optional[str] = None,
) -> TourAssignmentLog:
    log = TourAssignmentLog(
        tour_id=tour.id,
        guide_id=guide.id if guide else None,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=assigned_by,
        assignment_type=assignment_type,
        action=action,
    )
    db.add(log)
    db.flush()
    return log
