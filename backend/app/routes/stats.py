"""Stats routes -- dashboard aggregation endpoint."""

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("")
def read_stats(conn=Depends(get_db)):
    """Return today's dashboard metrics: tours, customers, cancellations, avg rating."""
    try:
        return stats_service.get_stats(conn)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
