import logging

from fastapi import APIRouter, HTTPException

from ..db import engine
from ..services import guide_requests as request_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guide", tags=["Guide Requests"])


@router.get("/swap-requests")
def read_swap_requests(guide_id: int):

    try:
        with engine.connect() as conn:
            return request_service.get_swap_requests(conn, guide_id)

    except Exception:
        logger.exception("Error loading swap requests")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/swap-request")
def create_swap_request(schedule_id: int, guide_id: int):

    try:
        with engine.connect() as conn:
            return request_service.create_swap_request(conn, schedule_id, guide_id)

    except Exception:
        logger.exception("Error creating swap request")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/swap-candidates")
def read_swap_candidates(schedule_id: int):

    try:
        with engine.connect() as conn:
            return request_service.get_swap_candidates(conn, schedule_id)

    except Exception:
        logger.exception("Error loading swap candidates")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/swap-accept")
def accept_swap_request(swap_request_id: int):

    try:
        with engine.connect() as conn:
            return request_service.accept_swap_request(conn, swap_request_id)

    except Exception:
        logger.exception("Error accepting swap request")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/swap-reject")
def reject_swap_request(swap_request_id: int):

    try:
        with engine.connect() as conn:
            return request_service.reject_swap_request(conn, swap_request_id)

    except Exception:
        logger.exception("Error rejecting swap request")
        raise HTTPException(status_code=500, detail="Internal server error")
