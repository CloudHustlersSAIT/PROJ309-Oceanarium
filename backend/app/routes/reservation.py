from datetime import date, time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services import reservation as reservation_service
from ..services.error_handlers import handle_domain_exception



class ReservationCreate(BaseModel):
    customer_id: int
    schedule_id: int
    adult_tickets: int
    child_tickets: int
    clorian_reservation_id: str | None = None
    clorian_purchase_id: int | None = None
    status: str | None = "CONFIRMED"


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


# New routes
@router.get("/reservations")
def read_reservations(conn=Depends(get_db)):
    try:
        return _read_reservations(conn)
    except Exception as e:
        handle_domain_exception(e)

@router.post("/reservations")
def create_reservation(
    payload: ReservationCreate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        return _create_reservation(payload, conn)
    except Exception as e:
        handle_domain_exception(e)

@router.patch("/reservations/{reservation_id}/reschedule")
def reschedule_reservation(
    reservation_id: int,
    payload: ReservationReschedule,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        return _reschedule_reservation(reservation_id, payload, conn)
    except Exception as e:
        handle_domain_exception(e)

@router.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        return _cancel_reservation(reservation_id, conn)
    except Exception as e:
        handle_domain_exception(e)

# Backward-compatible aliases (deprecated)
@router.get("/bookings", deprecated=True)
def read_bookings_legacy(conn=Depends(get_db)):
    return read_reservations(conn)


@router.post("/bookings", deprecated=True)
def create_booking_legacy(
    payload: ReservationCreate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    return create_reservation(payload, conn)


@router.patch("/bookings/{reservation_id}/reschedule", deprecated=True)
def reschedule_booking_legacy(
    reservation_id: int,
    payload: ReservationReschedule,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    return reschedule_reservation(reservation_id, payload, conn)


@router.patch("/bookings/{reservation_id}/cancel", deprecated=True)
def cancel_booking_legacy(
    reservation_id: int,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    return cancel_reservation(reservation_id, conn)
