from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.audit_log import TourAssignmentLog
from ..models.guide import Guide
from ..models.tour import Tour
from ..schemas.tour import ManualAssignIn
from ..services.assignment import manual_assign

router = APIRouter(prefix="/tours", tags=["Assignments"])


@router.post("/{tour_id}/assign")
def assign_guide(tour_id: int, payload: ManualAssignIn, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    guide = db.query(Guide).filter(Guide.id == payload.guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    manual_assign(tour, guide, db, assigned_by=payload.assigned_by)
    db.commit()
    return {
        "message": "Guide assigned",
        "tour_id": tour.id,
        "guide_id": guide.id,
        "status": tour.status,
    }


@router.post("/{tour_id}/reassign")
def reassign_guide(tour_id: int, payload: ManualAssignIn, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    guide = db.query(Guide).filter(Guide.id == payload.guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    manual_assign(tour, guide, db, assigned_by=payload.assigned_by)
    db.commit()
    return {
        "message": "Guide reassigned",
        "tour_id": tour.id,
        "guide_id": guide.id,
        "status": tour.status,
    }


@router.get("/{tour_id}/assignment-log")
def get_assignment_log(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    logs = (
        db.query(TourAssignmentLog)
        .filter(TourAssignmentLog.tour_id == tour_id)
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
