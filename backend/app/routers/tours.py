from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.tour import Tour
from ..schemas.tour import TourCreate, TourUpdate

router = APIRouter(prefix="/tours", tags=["Tours"])


@router.get("")
def list_tours(db: Session = Depends(get_db)):
    tours = db.query(Tour).all()
    return [_tour_to_dict(t) for t in tours]


@router.get("/{tour_id}")
def get_tour(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return _tour_to_dict(tour)


@router.post("", status_code=201)
def create_tour(payload: TourCreate, db: Session = Depends(get_db)):
    tour = Tour(
        name=payload.name,
        description=payload.description,
        duration=payload.duration,
    )
    db.add(tour)
    db.commit()
    db.refresh(tour)
    return _tour_to_dict(tour)


@router.patch("/{tour_id}")
def update_tour(tour_id: int, payload: TourUpdate, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    if payload.name is not None:
        tour.name = payload.name
    if payload.description is not None:
        tour.description = payload.description
    if payload.duration is not None:
        tour.duration = payload.duration

    db.commit()
    db.refresh(tour)
    return _tour_to_dict(tour)


@router.delete("/{tour_id}", status_code=204)
def delete_tour(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    db.delete(tour)
    db.commit()


def _tour_to_dict(tour: Tour) -> dict:
    return {
        "id": tour.id,
        "name": tour.name,
        "description": tour.description,
        "duration": tour.duration,
    }
