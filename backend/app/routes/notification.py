import logging

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import notification as notification_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def read_notifications(conn=Depends(get_db)):
    try:
        return notification_service.list_notifications(conn)
    except Exception as e:
        return handle_domain_exception(e)
