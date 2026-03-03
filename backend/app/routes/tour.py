from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import tour as tour_service

router = APIRouter(prefix="/tours", tags=["Tours"])


@router.get("")
def read_tours(conn=Depends(get_db)):
    try:
        return tour_service.list_tours(conn)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
