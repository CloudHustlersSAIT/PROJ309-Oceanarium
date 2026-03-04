import logging
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..services import reservation as reservation_service
from ..services.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class BookingCreate(BaseModel):
    customer_id: str
    tour_id: int
    date: date
    start_time: time
    end_time: time
    adult_tickets: int
    child_tickets: int


class BookingReschedule(BaseModel):
    new_date: date
    start_time: time
    end_time: time


router = APIRouter(prefix="/bookings", tags=["Reservations"])


@router.get("")
def read_bookings(conn=Depends(get_db)):
    try:
        return reservation_service.list_reservations(conn)
    except Exception:
        logger.exception("Unexpected error listing bookings")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
def create_booking(booking: BookingCreate, conn=Depends(get_db)):
    try:
        return reservation_service.create_reservation(conn, booking)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception:
        logger.exception("Unexpected error creating booking")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{booking_id}/reschedule")
def reschedule_booking(booking_id: int, reschedule: BookingReschedule, conn=Depends(get_db)):
    try:
        return reservation_service.reschedule_reservation(conn, booking_id, reschedule)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception:
        logger.exception("Unexpected error rescheduling booking")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int, conn=Depends(get_db)):
    try:
        return reservation_service.cancel_reservation(conn, booking_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception:
        logger.exception("Unexpected error cancelling booking")
        raise HTTPException(status_code=500, detail="Internal server error")
