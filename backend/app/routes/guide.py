import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services import guide as guide_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guides", tags=["Guides"])


class GuideCreate(BaseModel):
    first_name: str
    last_name: str
    email: str


class GuideUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


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
