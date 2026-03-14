from __future__ import annotations

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text

from ..db import get_db
from ..services import guide_assignment as guide_assignment_service
from ..services import notification as notification_service
from ..services import rescheduling as rescheduling_service
from ..services import schedule as schedule_service
from ..services.error_handlers import handle_domain_exception
from ..services.exceptions import UnassignableError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


class ScheduleCreate(BaseModel):
    # guide_id is optional because guide assignment can happen later.
    guide_id: int | None = None
    tour_id: int
    language_code: str
    event_start_datetime: datetime
    event_end_datetime: datetime
    status: str | None = "CONFIRMED"


@router.get("")
def read_schedules(
    start_date: date | None = Query(default=None, description="Filter events ending on/after this date (YYYY-MM-DD)"),
    end_date: date | None = Query(
        default=None,
        description="Filter events starting before next day of this date (YYYY-MM-DD)",
    ),
    status: str | None = Query(default=None, description="Filter by schedule status (case-insensitive exact match)"),
    guide_id: int | None = Query(default=None, description="Filter schedules by guide id"),
    scope: str | None = Query(
        default=None,
        description="When 'own', only return schedules for the given guide_id (guide_id is required)",
    ),
    conn=Depends(get_db),
):
    # When scope=own (guide portal), require guide_id so guides only see their own schedules.
    if scope == "own" and guide_id is None:
        handle_domain_exception(ValidationError("guide_id is required when scope=own"))
    try:
        return schedule_service.list_schedules(
            conn,
            start_date=start_date,
            end_date=end_date,
            status=status,
            guide_id=guide_id,
        )
    except Exception as e:
        return handle_domain_exception(e)


class ManualAssignRequest(BaseModel):
    guide_id: int
    reason: str | None = None


@router.post("")
def create_schedule(payload: ScheduleCreate, conn=Depends(get_db)):
    try:
        return schedule_service.create_schedule(conn, payload)
    except Exception as e:
        return handle_domain_exception(e)


@router.post("/auto-assign-all")
def auto_assign_all(conn=Depends(get_db)):
    """Run auto_assign_guide on every unassigned, non-cancelled schedule.

    For each schedule: assigns the best eligible guide and triggers a
    GUIDE_ASSIGNED notification, or triggers a SCHEDULE_UNASSIGNABLE
    notification if no guide qualifies.
    """
    rows = conn.execute(
        text("""
            SELECT id FROM schedule
            WHERE guide_id IS NULL
              AND status NOT IN ('CANCELLED')
            ORDER BY event_start_datetime
        """)
    ).fetchall()

    results = {
        "total": len(rows),
        "assigned": 0,
        "unassignable": 0,
        "errors": 0,
        "details": [],
    }

    for row in rows:
        sid = row[0]
        try:
            result = guide_assignment_service.auto_assign_guide(conn, sid)
            notification_service.notify_guide_assignment(conn, sid, result["guide_id"], "AUTO")
            results["assigned"] += 1
            results["details"].append(
                {
                    "schedule_id": sid,
                    "status": "assigned",
                    "guide_id": result["guide_id"],
                    "guide_name": result.get("guide_name"),
                }
            )
        except UnassignableError as e:
            notification_service.notify_schedule_unassignable(conn, sid, e.reasons)
            results["unassignable"] += 1
            results["details"].append(
                {
                    "schedule_id": sid,
                    "status": "unassignable",
                    "reasons": e.reasons,
                }
            )
        except Exception as e:
            logger.error(f"auto-assign-all error for schedule {sid}: {e}")
            results["errors"] += 1
            results["details"].append(
                {
                    "schedule_id": sid,
                    "status": "error",
                    "error": str(e),
                }
            )

    return results


@router.post("/{schedule_id}/assign")
def auto_assign(schedule_id: int, conn=Depends(get_db)):
    try:
        result = guide_assignment_service.auto_assign_guide(conn, schedule_id)

        # Trigger notification directly
        notification_service.notify_guide_assignment(conn, schedule_id, result["guide_id"], "AUTO")

        return result
    except UnassignableError as e:
        # Trigger unassignable notification
        notification_service.notify_schedule_unassignable(conn, schedule_id, e.reasons)
        return handle_domain_exception(e)
    except Exception as e:
        return handle_domain_exception(e)


@router.put("/{schedule_id}/assign")
def manual_assign(schedule_id: int, payload: ManualAssignRequest, conn=Depends(get_db)):
    try:
        result = guide_assignment_service.manual_assign_guide(
            conn,
            schedule_id,
            payload.guide_id,
            assigned_by="admin",
        )

        # Trigger notification directly
        notification_service.notify_guide_assignment(conn, schedule_id, payload.guide_id, "MANUAL")

        return result
    except Exception as e:
        return handle_domain_exception(e)


@router.get("/{schedule_id}/eligible-guides")
def get_eligible_guides(schedule_id: int, conn=Depends(get_db)):
    try:
        ranked, reasons = guide_assignment_service.find_eligible_guides(conn, schedule_id)
        guides = [{**g, "ranking_position": idx + 1} for idx, g in enumerate(ranked)]
        return {
            "schedule_id": schedule_id,
            "eligible_guides": guides,
            "reasons": reasons,
            "total": len(guides),
        }
    except Exception as e:
        return handle_domain_exception(e)


@router.delete("/{schedule_id}/guide")
def cancel_guide(schedule_id: int, conn=Depends(get_db)):
    try:
        result = rescheduling_service.handle_guide_cancellation(conn, schedule_id)

        # Trigger notifications based on result
        if result.get("old_guide_id"):
            notification_service.notify_guide_unassignment(
                conn, schedule_id, result["old_guide_id"], "Guide requested cancellation"
            )

        if result.get("new_guide_id"):
            notification_service.notify_guide_assignment(conn, schedule_id, result["new_guide_id"], "AUTO")
        elif result.get("status") == "UNASSIGNABLE":
            notification_service.notify_schedule_unassignable(conn, schedule_id, result.get("reasons", []))

        return result
    except Exception as e:
        return handle_domain_exception(e)
