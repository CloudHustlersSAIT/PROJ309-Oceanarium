import logging

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..services import guide as guide_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guides", tags=["Guides"])


@router.get("")
def read_guides(conn=Depends(get_db)):
    try:
        return guide_service.list_guides(conn)
    except Exception:
        logger.exception("Unexpected error listing guides")
        raise HTTPException(status_code=500, detail="Internal server error")
