"""
Guide Profile languages: view and edit languages spoken by a guide.

Does not modify scheduler, guide_assignment, poller, or availability logic.
Guide identity (guide_id) is taken from query parameter; in production
this should be derived from the authenticated user.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError

from ..db import engine
from ..services import guide_language_service as language_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guide", tags=["Guide Profile Languages"])


class LanguagesUpdateBody(BaseModel):
    language_ids: list[int]


@router.get("/profile/languages")
def get_profile_languages(guide_id: int):
    """
    Return the languages spoken by the guide for the profile page.
    """
    try:
        with engine.connect() as conn:
            return language_service.get_guide_languages(conn, guide_id)
    except OperationalError as e:
        logger.warning("Database unavailable for GET languages: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check that PostgreSQL is running and DATABASE_URL is correct.",
        ) from e
    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/profile/languages")
def update_profile_languages(guide_id: int, body: LanguagesUpdateBody):
    """
    Replace the guide's languages with the given list of language IDs.
    All changes in one transaction.
    """
    try:
        with engine.connect() as conn:
            language_service.update_guide_languages(conn, guide_id, body.language_ids)
        return {"ok": True, "message": "Languages updated"}
    except OperationalError as e:
        logger.warning("Database unavailable for PATCH languages: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check that PostgreSQL is running and DATABASE_URL is correct.",
        ) from e
    except Exception as e:
        logger.exception("PATCH /guide/profile/languages failed: %s", e)
        return handle_domain_exception(e)
