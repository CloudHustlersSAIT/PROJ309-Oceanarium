import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.booking import Booking
from ..models.booking_version import BookingVersion
from ..models.schedule import Schedule
from ..schemas.booking import BookingCreate, BookingReschedule
from ..services.clorian_sync import assign_unassigned_bookings
from ..services.guide_matcher import is_guide_available_on_date

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _compute_hash(booking_id, status, adult_tickets, child_tickets, start_date, start_time=None, end_time=None):
    raw = (
        f"{booking_id}|{status}|{adult_tickets}|{child_tickets}"
        f"|{start_date}|{start_time}|{end_time}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.get("")
def read_bookings(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    results = []
    for b in bookings:
        d = _booking_to_dict(b)
        if status is not None and d.get("status") != status:
            continue
        results.append(d)
    return results


@router.get("/unassigned")
def read_unassigned_bookings(db: Session = Depends(get_db)):
    bookings = (
        db.query(Booking)
        .filter(Booking.tour_id.is_(None))
        .order_by(Booking.created_at.desc())
        .all()
    )
    results = []
    for b in bookings:
        d = _booking_to_dict(b)
        if d.get("status") == "unassigned":
            results.append(d)
    return results


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
        customer_id=payload.customer_id,
        tour_id=payload.tour_id,
    )
    db.add(booking)
    db.flush()

    version_hash = _compute_hash(
        booking.booking_id,
        payload.status,
        payload.adult_tickets,
        payload.child_tickets,
        payload.start_date,
    )
    version = BookingVersion(
        booking_id=booking.booking_id,
        hash=version_hash,
        status=payload.status,
        adult_tickets=payload.adult_tickets,
        child_tickets=payload.child_tickets,
        start_date=payload.start_date,
        valid_from=datetime.now(timezone.utc),
    )
    db.add(version)
    db.commit()
    assign_unassigned_bookings(db)
    db.refresh(booking)
    return _booking_to_dict(booking)


@router.patch("/{booking_id}/reschedule")
def reschedule_booking(
    booking_id: int, payload: BookingReschedule, db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    lv = booking.latest_version
    status = lv.status if lv else "unassigned"
    adult = lv.adult_tickets if lv else 0
    child = lv.child_tickets if lv else 0
    s_time = lv.start_time if lv else None
    e_time = lv.end_time if lv else None
    old_schedules = list(lv.schedules) if lv else []

    guide_available = False
    if status == "assigned" and old_schedules:
        guide = old_schedules[0].guide
        guide_available = is_guide_available_on_date(guide, payload.new_date, db)
        if not guide_available:
            status = "unassigned"

    version_hash = _compute_hash(booking_id, status, adult, child, payload.new_date, s_time, e_time)
    version = BookingVersion(
        booking_id=booking.booking_id,
        hash=version_hash,
        status=status,
        adult_tickets=adult,
        child_tickets=child,
        start_date=payload.new_date,
        start_time=s_time,
        end_time=e_time,
        valid_from=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()

    for old_schedule in old_schedules:
        if guide_available:
            db.add(
                Schedule(
                    booking_version_id=version.id,
                    guide_id=old_schedule.guide_id,
                    resource_id=old_schedule.resource_id,
                    start_date=datetime.combine(payload.new_date, datetime.min.time()),
                    end_date=datetime.combine(payload.new_date, datetime.min.time()),
                )
            )
        db.delete(old_schedule)

    db.commit()
    assign_unassigned_bookings(db)
    db.refresh(booking)
    return _booking_to_dict(booking)


@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    lv = booking.latest_version
    adult = lv.adult_tickets if lv else 0
    child = lv.child_tickets if lv else 0
    start = lv.start_date if lv else datetime.now(timezone.utc).date()
    s_time = lv.start_time if lv else None
    e_time = lv.end_time if lv else None
    old_schedules = list(lv.schedules) if lv else []

    version_hash = _compute_hash(booking_id, "cancelled", adult, child, start, s_time, e_time)
    version = BookingVersion(
        booking_id=booking.booking_id,
        hash=version_hash,
        status="cancelled",
        adult_tickets=adult,
        child_tickets=child,
        start_date=start,
        start_time=s_time,
        end_time=e_time,
        valid_from=datetime.now(timezone.utc),
    )
    db.add(version)

    for old_schedule in old_schedules:
        db.delete(old_schedule)

    db.commit()
    assign_unassigned_bookings(db)
    db.refresh(booking)
    return _booking_to_dict(booking)


def _booking_to_dict(booking: Booking) -> dict:
    lv = booking.latest_version
    guide_name = None
    if lv and lv.schedules:
        guide = lv.schedules[0].guide
        if guide:
            guide_name = f"{guide.first_name} {guide.last_name}"

    customer_name = None
    if booking.customer:
        customer_name = f"{booking.customer.first_name} {booking.customer.last_name}"

    tour_name = None
    if booking.tour:
        tour_name = booking.tour.name

    return {
        "booking_id": booking.booking_id,
        "clorian_booking_id": booking.clorian_booking_id,
        "customer_id": booking.customer_id,
        "customer_name": customer_name,
        "tour_id": booking.tour_id,
        "tour_name": tour_name,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
        "date": lv.start_date.isoformat() if lv else None,
        "start_time": lv.start_time.strftime("%H:%M") if lv and lv.start_time else None,
        "end_time": lv.end_time.strftime("%H:%M") if lv and lv.end_time else None,
        "adult_tickets": lv.adult_tickets if lv else 0,
        "child_tickets": lv.child_tickets if lv else 0,
        "status": lv.status if lv else "unassigned",
        "guide_name": guide_name,
    }
