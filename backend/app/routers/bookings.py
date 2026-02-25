from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.booking import Booking
from ..schemas.booking import BookingCreate, BookingReschedule

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("")
def read_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    return [_booking_to_dict(b) for b in bookings]


@router.post("", status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    booking = Booking(
        customer_id=payload.customer_id,
        tour_id=payload.tour_id,
        date=payload.date,
        adult_tickets=payload.adult_tickets,
        child_tickets=payload.child_tickets,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_to_dict(booking)


@router.patch("/{booking_id}/reschedule")
def reschedule_booking(
    booking_id: int, payload: BookingReschedule, db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.date = payload.new_date
    db.commit()
    db.refresh(booking)
    return _booking_to_dict(booking)


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return _booking_to_dict(booking)


def _booking_to_dict(booking: Booking) -> dict:
    return {
        "booking_id": booking.booking_id,
        "customer_id": booking.customer_id,
        "tour_id": booking.tour_id,
        "date": booking.date.isoformat(),
        "adult_tickets": booking.adult_tickets,
        "child_tickets": booking.child_tickets,
        "status": booking.status,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
    }
