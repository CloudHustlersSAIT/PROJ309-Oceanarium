import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..db import get_db
from ..services import schedule as schedule_service
from ..services.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


class ScheduleCreate(BaseModel):
    guide_id: Optional[int] = None
    tour_id: int
    language_code: str
    event_start_datetime: datetime
    event_end_datetime: datetime
    status: Optional[str] = "CONFIRMED"


@router.get("")
def read_schedules(
    start_date: date | None = Query(default=None, description="Filter events ending on/after this date (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="Filter events starting before next day of this date (YYYY-MM-DD)"),
    status: str | None = Query(default=None, description="Filter by schedule status (case-insensitive exact match)"),
    conn=Depends(get_db),
):
    try:
        return schedule_service.list_schedules(
            conn,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception:
        logger.exception("Unexpected error listing schedules")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
def create_schedule(payload: ScheduleCreate, conn=Depends(get_db)):
    try:
        return schedule_service.create_schedule(conn, payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception:
        logger.exception("Unexpected error creating schedule")
        raise HTTPException(status_code=500, detail="Internal server error")