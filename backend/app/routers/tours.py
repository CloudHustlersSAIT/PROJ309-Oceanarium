from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tour import Tour

router = APIRouter(prefix="/tours", tags=["Tours"])


@router.get("")
def list_tours(db: Session = Depends(get_db)):
    tours = db.query(Tour).order_by(Tour.date, Tour.start_time).all()
    return [_tour_to_dict(t) for t in tours]


@router.get("/unassigned")
def list_unassigned_tours(db: Session = Depends(get_db)):
    tours = (
        db.query(Tour)
        .filter(Tour.status == "unassigned")
        .order_by(Tour.date, Tour.start_time)
        .all()
    )
    return [_tour_to_dict(t) for t in tours]


@router.get("/{tour_id}")
def get_tour(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return _tour_to_dict(tour)


def _tour_to_dict(tour: Tour) -> dict:
    return {
        "id": tour.id,
        "clorian_booking_id": tour.clorian_booking_id,
        "date": tour.date.isoformat(),
        "start_time": tour.start_time.strftime("%H:%M"),
        "end_time": tour.end_time.strftime("%H:%M"),
        "required_expertise": tour.required_expertise,
        "required_category": tour.required_category,
        "requested_language_code": tour.requested_language_code,
        "status": tour.status,
        "assigned_guide_id": tour.assigned_guide_id,
        "assigned_guide_name": tour.assigned_guide.name if tour.assigned_guide else None,
    }
