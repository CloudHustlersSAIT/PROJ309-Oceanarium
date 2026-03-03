"""Reservation routes -- CRUD endpoints for the bookings table.

Provides listing, creation, rescheduling, and cancellation of bookings.
All business logic lives in ``services.reservation``; this module only
parses requests, delegates to the service, and maps domain exceptions to
HTTP status codes.

Note: Endpoint paths use ``/bookings`` for backward compatibility even
though the file is named ``reservation.py`` (ADR-001 domain naming).

Pydantic schemas (``BookingCreate``, ``BookingReschedule``) live here
temporarily until Phase 3 extracts them to a dedicated ``schemas/`` layer.
"""

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..services import reservation as reservation_service
from ..services.exceptions import ConflictError, NotFoundError, ValidationError


class BookingCreate(BaseModel):
    """Request body for creating a new booking."""

    customer_id: str
    tour_id: int
    date: date
    start_time: time
    end_time: time
    adult_tickets: int
    child_tickets: int


class BookingReschedule(BaseModel):
    """Request body for rescheduling an existing booking."""

    new_date: date
    start_time: time
    end_time: time


router = APIRouter(prefix="/bookings", tags=["Reservations"])


@router.get("")
def read_bookings(conn=Depends(get_db)):
    """List all bookings ordered by creation date (newest first)."""
    try:
        return reservation_service.list_reservations(conn)
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("")
def create_booking(booking: BookingCreate, conn=Depends(get_db)):
    """Create a new booking with ticket validation and guide conflict detection."""
    try:
        return reservation_service.create_reservation(conn, booking)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.patch("/{booking_id}/reschedule")
def reschedule_booking(booking_id: int, reschedule: BookingReschedule, conn=Depends(get_db)):
    """Move an existing booking to a new date/time, re-checking for conflicts."""
    try:
        return reservation_service.reschedule_reservation(conn, booking_id, reschedule)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int, conn=Depends(get_db)):
    """Cancel a booking. Returns 400 if already cancelled, 404 if not found."""
    try:
        return reservation_service.cancel_reservation(conn, booking_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
