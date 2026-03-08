import logging
from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..services import reservation as reservation_service
from ..services.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class BookingCreate(BaseModel):
    customer_id: int
    tour_id: int
    language: Optional[str] = None
    date: date
    start_time: time
    end_time: time
class ReservationCreate(BaseModel):
    customer_id: int
    schedule_id: int
    adult_tickets: int
    child_tickets: int
    clorian_reservation_id: Optional[str] = None
    clorian_purchase_id: Optional[int] = None
    status: Optional[str] = "CONFIRMED"


class BookingReschedule(BaseModel):
    new_date: date
    start_time: time
    end_time: time
class ReservationReschedule(BaseModel):
    new_schedule_id: int


router = APIRouter(tags=["Reservations"])

# Shared implementation helpers (single source of behavior)


def _read_reservations(conn):
    return reservation_service.list_reservations(conn)


def _create_reservation(payload, conn):
    return reservation_service.create_reservation(conn, payload)


def _reschedule_reservation(reservation_id, payload, conn):
    return reservation_service.reschedule_reservation(conn, reservation_id, payload)


def _cancel_reservation(reservation_id, conn):
    return reservation_service.cancel_reservation(conn, reservation_id)

# New canonical routes


# New routes
@router.get("/reservations")
def read_reservations(conn=Depends(get_db)):
    try:
        return _read_reservations(conn)
    except Exception:
        logger.exception("Unexpected error listing reservations")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reservations")
def create_reservation(payload: ReservationCreate, conn=Depends(get_db)):
    try:
        return _create_reservation(payload, conn)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception:
        logger.exception("Unexpected error creating reservation")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/reservations/{reservation_id}/reschedule")
def reschedule_reservation(reservation_id: int, payload: ReservationReschedule, conn=Depends(get_db)):
    try:
        return _reschedule_reservation(reservation_id, payload, conn)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception:
        logger.exception("Unexpected error rescheduling reservation")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, conn=Depends(get_db)):
    try:
        return _cancel_reservation(reservation_id, conn)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception:
        logger.exception("Unexpected error cancelling reservation")
        raise HTTPException(status_code=500, detail="Internal server error")

# Backward-compatible aliases (deprecated)


@router.get("/bookings", deprecated=True)
def read_bookings_legacy(conn=Depends(get_db)):
    return read_reservations(conn)


@router.post("/bookings", deprecated=True)
def create_booking_legacy(payload: ReservationCreate, conn=Depends(get_db)):
    return create_reservation(payload, conn)


@router.patch("/bookings/{reservation_id}/reschedule", deprecated=True)
def reschedule_booking_legacy(reservation_id: int, payload: ReservationReschedule, conn=Depends(get_db)):
    return reschedule_reservation(reservation_id, payload, conn)


@router.patch("/bookings/{reservation_id}/cancel", deprecated=True)
def cancel_booking_legacy(reservation_id: int, conn=Depends(get_db)):
    return cancel_reservation(reservation_id, conn)
