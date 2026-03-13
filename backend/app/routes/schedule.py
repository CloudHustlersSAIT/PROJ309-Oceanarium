from __future__ import annotations

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..db import get_db
from ..services import guide_assignment as guide_assignment_service
from ..services import rescheduling as rescheduling_service
from ..services import schedule as schedule_service
from ..services.error_handlers import handle_domain_exception

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
    conn=Depends(get_db),
):
    # Thin route: delegate filtering/query logic to service layer.
    try:
        return schedule_service.list_schedules(
            conn,
            start_date=start_date,
            end_date=end_date,
            status=status,
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


@router.post("/{schedule_id}/assign")
def auto_assign(schedule_id: int, conn=Depends(get_db)):
    try:
        return guide_assignment_service.auto_assign_guide(conn, schedule_id)
    except Exception as e:
        return handle_domain_exception(e)


@router.put("/{schedule_id}/assign")
def manual_assign(schedule_id: int, payload: ManualAssignRequest, conn=Depends(get_db)):
    try:
        return guide_assignment_service.manual_assign_guide(
            conn,
            schedule_id,
            payload.guide_id,
            assigned_by="admin",
        )
    except Exception as e:
        return handle_domain_exception(e)


@router.delete("/{schedule_id}/guide")
def cancel_guide(schedule_id: int, conn=Depends(get_db)):
    try:
        return rescheduling_service.handle_guide_cancellation(conn, schedule_id)
    except Exception as e:
        return handle_domain_exception(e)
