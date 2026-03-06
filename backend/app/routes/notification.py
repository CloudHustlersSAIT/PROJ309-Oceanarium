import logging

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services import notification as notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def read_notifications(conn=Depends(get_db)):
    try:
        return notification_service.list_notifications(conn)
    except Exception:
        logger.exception("Unexpected error listing notifications")
        raise HTTPException(status_code=500, detail="Internal server error")
