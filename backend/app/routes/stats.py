import logging

from fastapi import APIRouter, Depends

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
