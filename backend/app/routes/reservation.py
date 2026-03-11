from datetime import date, time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import get_db
from ..services import reservation as reservation_service
from ..services.error_handlers import handle_domain_exception


class BookingCreate(BaseModel):
    customer_id: int
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
@router.get("/reservations")
def read_reservations(conn=Depends(get_db)):
    try:
        return _read_reservations(conn)
    except Exception as e:
        handle_domain_exception(e)

@router.post("/reservations")
def create_reservation(payload: BookingCreate, conn=Depends(get_db)):
    try:
        return _create_reservation(payload, conn)
    except Exception as e:
        handle_domain_exception(e)

@router.patch("/reservations/{reservation_id}/reschedule")
def reschedule_reservation(reservation_id: int, payload: BookingReschedule, conn=Depends(get_db)):
    try:
        return _reschedule_reservation(reservation_id, payload, conn)
    except Exception as e:
        handle_domain_exception(e)

@router.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, conn=Depends(get_db)):
    try:
        return _cancel_reservation(reservation_id, conn)
    except Exception as e:
        handle_domain_exception(e)

# Backward-compatible aliases (deprecated)
@router.get("/bookings", deprecated=True)
def read_bookings_legacy(conn=Depends(get_db)):
    return read_reservations(conn)

@router.post("/bookings", deprecated=True)
def create_booking_legacy(payload: BookingCreate, conn=Depends(get_db)):
    return create_reservation(payload, conn)

@router.patch("/bookings/{reservation_id}/reschedule", deprecated=True)
def reschedule_booking_legacy(reservation_id: int, payload: BookingReschedule, conn=Depends(get_db)):
    return reschedule_reservation(reservation_id, payload, conn)

@router.patch("/bookings/{reservation_id}/cancel", deprecated=True)
def cancel_booking_legacy(reservation_id: int, conn=Depends(get_db)):
    return cancel_reservation(reservation_id, conn)