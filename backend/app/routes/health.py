"""Health-check routes.

Provides liveness (``/health``) and database readiness (``/health/db``)
endpoints used by monitoring, load balancers, and Docker health checks.
"""

from fastapi import APIRouter

from ..db import test_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """Return a simple liveness probe -- always ``{"status": "ok"}``."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db():
    """Verify database connectivity by running ``SELECT 1``.

    Returns ``{"status": "ok", "db_check": 1}`` on success, or
    ``{"status": "error", "detail": "..."}`` if the connection fails.
    """
    try:
        value = test_connection()
        return {"status": "ok", "db_check": value}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
