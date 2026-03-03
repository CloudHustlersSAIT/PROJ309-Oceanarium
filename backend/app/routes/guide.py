"""Guide routes -- read-only endpoint for listing guides."""

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import guide as guide_service

router = APIRouter(prefix="/guides", tags=["Guides"])


@router.get("")
def read_guides(conn=Depends(get_db)):
    """Return all guides ordered alphabetically by name."""
    try:
        return guide_service.list_guides(conn)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
