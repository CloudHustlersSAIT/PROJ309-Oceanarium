import logging
from datetime import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services import guide as guide_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guides", tags=["Guides"])


class AvailabilitySlotPayload(BaseModel):
    day_of_week: str
    start_time: time
    end_time: time


class AvailabilityPatternPayload(BaseModel):
    timezone: str
    slots: list[AvailabilitySlotPayload] = Field(default_factory=list)


class GuideCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    language_codes: list[str] = Field(default_factory=list)
    expertise_tour_ids: list[int] = Field(default_factory=list)
    availability_patterns: list[AvailabilityPatternPayload] = Field(default_factory=list)


class GuideUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    language_codes: list[str] | None = None
    expertise_tour_ids: list[int] | None = None
    availability_patterns: list[AvailabilityPatternPayload] | None = None


@router.get("")
def read_guides(conn=Depends(get_db)):
    try:
        return guide_service.list_guides(conn)
    except Exception as e:
        return handle_domain_exception(e)


@router.post("")
def create_guide(
    payload: GuideCreate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        return guide_service.create_guide(
            conn,
            payload.first_name,
            payload.last_name,
            payload.email,
            payload.phone,
            payload.language_codes,
            payload.expertise_tour_ids,
            [pattern.model_dump() for pattern in payload.availability_patterns],
        )
    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/{guide_id}")
def edit_guide(
    guide_id: int,
    payload: GuideUpdate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        updated = guide_service.update_guide(
            conn,
            guide_id,
            payload.model_dump(exclude_none=True),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Guide not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        return handle_domain_exception(e)
