import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db import get_db
from ..services import schedule as schedule_service
from ..services.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


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