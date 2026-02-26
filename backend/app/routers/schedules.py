from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.schedule import Schedule
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("")
def list_schedules(
    guide_id: Optional[int] = Query(None),
    booking_version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Schedule)
    if guide_id is not None:
        query = query.filter(Schedule.guide_id == guide_id)
    if booking_version_id is not None:
        query = query.filter(Schedule.booking_version_id == booking_version_id)
    return [_schedule_to_dict(s) for s in query.all()]


@router.get("/{schedule_id}")
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _schedule_to_dict(schedule)


@router.post("", status_code=201)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    schedule = Schedule(
        booking_version_id=payload.booking_version_id,
        guide_id=payload.guide_id,
        resource_id=payload.resource_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return _schedule_to_dict(schedule)


@router.patch("/{schedule_id}")
def update_schedule(schedule_id: int, payload: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if payload.guide_id is not None:
        schedule.guide_id = payload.guide_id
    if payload.resource_id is not None:
        schedule.resource_id = payload.resource_id
    if payload.start_date is not None:
        schedule.start_date = payload.start_date
    if payload.end_date is not None:
        schedule.end_date = payload.end_date

    db.commit()
    db.refresh(schedule)
    return _schedule_to_dict(schedule)


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()


def _schedule_to_dict(schedule: Schedule) -> dict:
    return {
        "id": schedule.id,
        "booking_version_id": schedule.booking_version_id,
        "guide_id": schedule.guide_id,
        "resource_id": schedule.resource_id,
        "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
        "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
    }
