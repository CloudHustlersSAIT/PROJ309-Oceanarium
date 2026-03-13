"""
Guide Profile availability: view and edit weekly availability.

Does not modify scheduler, poller, or assignment logic.
Guide identity (guide_id) is taken from query parameter; in production
this should be derived from the authenticated user.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError

from ..db import engine
from ..services import guide_availability_service as availability_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guide", tags=["Guide Profile Availability"])


class AvailabilitySlotUpdate(BaseModel):
    day: str
    start: str
    end: str


class AvailabilityUpdateBody(BaseModel):
    slots: list[AvailabilitySlotUpdate]
    timezone: str | None = None  # optional; accepted but not yet used when updating


@router.get("/profile/availability")
def get_profile_availability(guide_id: int):
    """
    Return the guide's availability (timezone and slots) for the profile page.
    Uses the first availability_pattern for the guide; empty slots if none exists.
    """
    try:
        with engine.connect() as conn:
            return availability_service.get_guide_availability(conn, guide_id)
    except OperationalError as e:
        logger.warning("Database unavailable for GET availability: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check that PostgreSQL is running and DATABASE_URL is correct.",
        ) from e
    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/profile/availability")
def update_profile_availability(guide_id: int, body: AvailabilityUpdateBody):
    """
    Replace the guide's availability slots. Creates an availability_pattern
    with default timezone (UTC) if the guide has none. All changes in one transaction.
    """
    try:
        slots = [{"day": s.day, "start": s.start, "end": s.end} for s in body.slots]
        with engine.connect() as conn:
            availability_service.update_guide_availability(conn, guide_id, slots)
        return {"ok": True, "message": "Availability updated"}
    except OperationalError as e:
        logger.warning("Database unavailable for PATCH availability: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check that PostgreSQL is running and DATABASE_URL is correct.",
        ) from e
    except Exception as e:
        logger.exception("PATCH /guide/profile/availability failed: %s", e)
        return handle_domain_exception(e)
