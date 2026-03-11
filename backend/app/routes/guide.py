import logging

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import guide as guide_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guides", tags=["Guides"])


@router.get("")
def read_guides(conn=Depends(get_db)):
    try:
        return guide_service.list_guides(conn)
    except Exception as e:
        return handle_domain_exception(e)
