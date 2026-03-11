import logging

from fastapi import APIRouter

from ..db import test_connection

from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db():
    try:
        value = test_connection()
        if value is None:
            raise HTTPException(status_code=500, detail="Database unavailable")
        return {"status": "ok", "db_check": value}
    except Exception as e:
        return handle_domain_exception(e)
