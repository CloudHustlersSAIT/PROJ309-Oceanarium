from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def read_notifications(conn=Depends(get_db)):
    try:
        return notification_service.list_notifications(conn)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
