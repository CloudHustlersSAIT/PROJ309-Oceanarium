import logging

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import tour as tour_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tours", tags=["Tours"])


@router.get("")
def read_tours(conn=Depends(get_db)):
    try:
        return tour_service.list_tours(conn)
    except Exception as e:
        return handle_domain_exception(e)
