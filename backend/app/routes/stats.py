import logging

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services import stats as stats_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("")
def read_stats(conn=Depends(get_db)):
    try:
        return stats_service.get_stats(conn)
    except Exception:
        logger.exception("Unexpected error fetching stats")
        raise HTTPException(status_code=500, detail="Internal server error") from None
