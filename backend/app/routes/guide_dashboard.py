import logging

from fastapi import APIRouter

from ..db import engine
from ..services import guide_dashboard as dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guide", tags=["Guide Dashboard"])


@router.get("/dashboard")
def read_dashboard(guide_id: int):

    try:
        with engine.connect() as conn:
            return dashboard_service.get_dashboard(conn, guide_id)

    except Exception:
        logger.exception("Error loading dashboard")
        return {"error": "Internal server error"}
