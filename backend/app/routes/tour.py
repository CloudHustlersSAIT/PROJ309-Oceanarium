import logging

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services import tour as tour_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tours", tags=["Tours"])


@router.get("")
def read_tours(conn=Depends(get_db)):
    try:
        return tour_service.list_tours(conn)
    except Exception:
        logger.exception("Unexpected error listing tours")
        raise HTTPException(status_code=500, detail="Internal server error")
