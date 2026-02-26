from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models.booking import Booking
from ..models.tour import Tour
from ..schemas.booking import VALID_BOOKING_STATUSES, BookingCreate, BookingReschedule

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("")
def read_bookings(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Booking).options(
        joinedload(Booking.tour).joinedload(Tour.assigned_guide)
    )
    if status is not None:
        query = query.filter(Booking.status == status)
    bookings = query.order_by(Booking.created_at.desc()).all()
    return [_booking_to_dict(b) for b in bookings]


@router.get("/unassigned")
def read_unassigned_bookings(db: Session = Depends(get_db)):
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.tour).joinedload(Tour.assigned_guide))
        .filter(Booking.status == "pending", Booking.tour_id.is_(None))
        .order_by(Booking.created_at.desc())
        .all()
    )
    return [_booking_to_dict(b) for b in bookings]


@router.post("", status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Booking)
        .filter(Booking.clorian_booking_id == payload.clorian_booking_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Booking with clorian_booking_id '{payload.clorian_booking_id}' already exists",
        )

    booking = Booking(
        clorian_booking_id=payload.clorian_booking_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        required_expertise=payload.required_expertise,
        required_category=payload.required_category,
        requested_language_code=payload.requested_language_code,
        customer_id=payload.customer_id,
        adult_tickets=payload.adult_tickets,
        child_tickets=payload.child_tickets,
        status="pending",
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


@router.patch("/{booking_id}/complete")
def complete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "assigned":
        raise HTTPException(
            status_code=400,
            detail="Only assigned bookings can be marked as completed",
        )

    booking.status = "completed"
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
    guide_name = None
    if booking.tour and booking.tour.assigned_guide:
        guide_name = booking.tour.assigned_guide.name
    return {
        "booking_id": booking.booking_id,
        "clorian_booking_id": booking.clorian_booking_id,
        "date": booking.date.isoformat(),
        "start_time": booking.start_time.strftime("%H:%M"),
        "end_time": booking.end_time.strftime("%H:%M"),
        "required_expertise": booking.required_expertise,
        "required_category": booking.required_category,
        "requested_language_code": booking.requested_language_code,
        "customer_id": booking.customer_id,
        "adult_tickets": booking.adult_tickets,
        "child_tickets": booking.child_tickets,
        "status": booking.status,
        "tour_id": booking.tour_id,
        "guide_name": guide_name,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
    }
