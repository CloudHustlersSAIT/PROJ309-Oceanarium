from fastapi import APIRouter

from ..db import test_connection, engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db():
    try:
        value = test_connection()
        return {"status": "ok", "db_check": value}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
