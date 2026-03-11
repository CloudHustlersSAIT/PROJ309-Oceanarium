from __future__ import annotations

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services import schedule as schedule_service
from ..services.exceptions import ConflictError, NotFoundError, ValidationError

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
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message) from e
    except Exception:
        logger.exception("Unexpected error listing schedules")
        raise HTTPException(status_code=500, detail="Internal server error") from None


@router.post("")
def create_schedule(
    payload: ScheduleCreate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    # Thin route: map domain exceptions to HTTP responses.
    try:
        return schedule_service.create_schedule(conn, payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message) from e
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message) from e
    except Exception:
        logger.exception("Unexpected error creating schedule")
        raise HTTPException(status_code=500, detail="Internal server error") from None
