from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.audit_log import TourAssignmentLog
from ..models.booking import Booking
from ..models.booking_version import BookingVersion
from ..models.guide import Guide
from ..models.schedule import Schedule
from ..schemas.tour import ManualAssignIn
from ..services.assignment import manual_assign, release_guide_from_schedule
from ..services.clorian_sync import assign_unassigned_bookings

router = APIRouter(prefix="/bookings", tags=["Assignments"])


@router.post("/{booking_id}/assign")
def assign_guide(booking_id: int, payload: ManualAssignIn, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    lv = booking.latest_version
    if not lv:
        raise HTTPException(status_code=400, detail="Booking has no version")

    guide = db.query(Guide).filter(Guide.id == payload.guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    schedule = manual_assign(lv, guide, db, assigned_by=payload.assigned_by)
    db.commit()
    return {
        "message": "Guide assigned",
        "booking_id": booking.booking_id,
        "guide_id": guide.id,
        "schedule_id": schedule.id,
    }


@router.post("/{booking_id}/reassign")
def reassign_guide(booking_id: int, payload: ManualAssignIn, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    lv = booking.latest_version
    if not lv:
        raise HTTPException(status_code=400, detail="Booking has no version")

    guide = db.query(Guide).filter(Guide.id == payload.guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    schedule = manual_assign(lv, guide, db, assigned_by=payload.assigned_by)
    db.commit()
    return {
        "message": "Guide reassigned",
        "booking_id": booking.booking_id,
        "guide_id": guide.id,
        "schedule_id": schedule.id,
    }


@router.post("/auto-assign")
def auto_assign(db: Session = Depends(get_db)):
    assigned_count = assign_unassigned_bookings(db)
    return {
        "message": f"{assigned_count} booking(s) auto-assigned",
        "assigned_count": assigned_count,
    }


@router.get("/{booking_id}/assignment-log")
def get_assignment_log(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if not booking.tour_id:
        return []

    logs = (
        db.query(TourAssignmentLog)
        .filter(TourAssignmentLog.tour_id == booking.tour_id)
        .order_by(TourAssignmentLog.assigned_at)
        .all()
    )
    return [
        {
            "id": log.id,
            "tour_id": log.tour_id,
            "guide_id": log.guide_id,
            "assigned_at": log.assigned_at.isoformat() if log.assigned_at else None,
            "assigned_by": log.assigned_by,
            "assignment_type": log.assignment_type,
            "action": log.action,
        }
        for log in logs
    ]
