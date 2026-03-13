import logging

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import language as language_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("")
def read_languages(conn=Depends(get_db)):
    try:
        return language_service.list_languages(conn)
    except Exception as e:
        return handle_domain_exception(e)
