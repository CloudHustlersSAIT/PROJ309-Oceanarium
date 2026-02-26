from fastapi import APIRouter
from sqlalchemy import text

from ..db import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            max_conn = conn.execute(text("SHOW max_connections")).scalar()
            active_conn = conn.execute(
                text("SELECT count(*) FROM pg_stat_activity")
            ).scalar()

        return {
            "status": "ok",
            "db_version": version,
            "max_connections": int(max_conn),
            "active_connections": active_conn,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
