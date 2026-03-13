from typing import Optional
import logging
from datetime import date

from fastapi import APIRouter, Depends, Query

from ..db import get_db
from ..services import stats as stats_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("")
def read_stats(conn=Depends(get_db)):
    try:
        return stats_service.get_stats(conn)
    except Exception as e:
        return handle_domain_exception(e)


@router.get("/admin-dashboard")
def read_admin_dashboard(
    selected_date: Optional[date] = Query(default=None, description="Anchor date for dashboard aggregations (YYYY-MM-DD)"),
    period: Optional[str] = Query(
        default="all_time",
        description="Aggregation window: all_time, this_month, this_week, this_day",
    ),
    conn=Depends(get_db),
):
    try:
        return stats_service.get_admin_dashboard(conn, selected_date=selected_date, period=period)
    except Exception as e:
        return handle_domain_exception(e)
