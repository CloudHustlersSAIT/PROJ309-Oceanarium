import logging

from fastapi import APIRouter, HTTPException

from ..db import test_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db():
    try:
        value = test_connection()
        return {"status": "ok", "db_check": value}
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=500, detail="Internal server error")
