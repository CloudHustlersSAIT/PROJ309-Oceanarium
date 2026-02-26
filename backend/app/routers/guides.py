from datetime import date as date_type
from datetime import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.availability import (
    AvailabilityException,
    AvailabilityPattern,
    AvailabilitySlot,
)
from ..models.guide import Expertise, Guide, Language
from ..models.tour import Tour
from ..schemas.guide import (
    AvailabilitySetIn,
    GuideCreate,
    GuideOut,
    GuideUpdate,
)
from ..services.clorian_sync import assign_unassigned_bookings

router = APIRouter(prefix="/guides", tags=["Guides"])


@router.get("", response_model=list)
def list_guides(db: Session = Depends(get_db)):
    guides = db.query(Guide).all()
    return [_guide_to_dict(g) for g in guides]


@router.post("", status_code=201)
def create_guide(payload: GuideCreate, db: Session = Depends(get_db)):
    guide = Guide(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        guide_rating=payload.guide_rating,
        is_active=payload.is_active,
    )
    db.add(guide)
    db.flush()

    _sync_languages(db, guide, payload.languages)
    _sync_expertises(db, guide, payload.expertises)
    _sync_tour_types(db, guide, payload.tour_type_ids)

    db.commit()
    db.refresh(guide)
    assign_unassigned_bookings(db)
    return _guide_to_dict(guide)


@router.get("/{guide_id}")
def get_guide(guide_id: int, db: Session = Depends(get_db)):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _guide_to_dict(guide)


@router.patch("/{guide_id}")
def update_guide(guide_id: int, payload: GuideUpdate, db: Session = Depends(get_db)):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    if payload.first_name is not None:
        guide.first_name = payload.first_name
    if payload.last_name is not None:
        guide.last_name = payload.last_name
    if payload.email is not None:
        guide.email = payload.email
    if payload.phone is not None:
        guide.phone = payload.phone
    if payload.guide_rating is not None:
        guide.guide_rating = payload.guide_rating
    if payload.is_active is not None:
        guide.is_active = payload.is_active

    if payload.languages is not None:
        guide.languages.clear()
        _sync_languages(db, guide, payload.languages)

    if payload.expertises is not None:
        guide.expertises.clear()
        _sync_expertises(db, guide, payload.expertises)

    if payload.tour_type_ids is not None:
        guide.tour_types.clear()
        _sync_tour_types(db, guide, payload.tour_type_ids)

    db.commit()
    db.refresh(guide)
    assign_unassigned_bookings(db)
    return _guide_to_dict(guide)


@router.put("/{guide_id}/availability")
def set_availability(
    guide_id: int, payload: AvailabilitySetIn, db: Session = Depends(get_db)
):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    if guide.availability_pattern:
        db.delete(guide.availability_pattern)
        db.flush()

    pattern = AvailabilityPattern(guide_id=guide.id, timezone=payload.timezone)
    db.add(pattern)
    db.flush()

    for s in payload.slots:
        parts_start = s.start_time.split(":")
        parts_end = s.end_time.split(":")
        slot = AvailabilitySlot(
            pattern_id=pattern.id,
            day_of_week=s.day_of_week,
            start_time=time(int(parts_start[0]), int(parts_start[1])),
            end_time=time(int(parts_end[0]), int(parts_end[1])),
        )
        db.add(slot)

    for e in payload.exceptions:
        exc = AvailabilityException(
            pattern_id=pattern.id,
            date=date_type.fromisoformat(e.date),
            type=e.type,
            reason=e.reason,
        )
        db.add(exc)

    db.commit()
    db.refresh(guide)
    assign_unassigned_bookings(db)
    return _guide_to_dict(guide)


def _sync_languages(db, guide, language_codes):
    for code in language_codes:
        lang = db.query(Language).filter(Language.code == code).first()
        if not lang:
            lang = Language(code=code, name=code)
            db.add(lang)
            db.flush()
        guide.languages.append(lang)


def _sync_expertises(db, guide, expertises):
    for exp_in in expertises:
        exp = db.query(Expertise).filter(Expertise.name == exp_in.name).first()
        if not exp:
            exp = Expertise(name=exp_in.name, category=exp_in.category)
            db.add(exp)
            db.flush()
        guide.expertises.append(exp)


def _sync_tour_types(db, guide, tour_type_ids):
    for tid in tour_type_ids:
        tour = db.query(Tour).filter(Tour.id == tid).first()
        if tour and tour not in guide.tour_types:
            guide.tour_types.append(tour)


def _guide_to_dict(guide: Guide) -> dict:
    result = {
        "id": guide.id,
        "first_name": guide.first_name,
        "last_name": guide.last_name,
        "email": guide.email,
        "phone": guide.phone,
        "guide_rating": float(guide.guide_rating) if guide.guide_rating else 0,
        "is_active": guide.is_active,
        "languages": [{"id": l.id, "code": l.code, "name": l.name} for l in guide.languages],
        "expertises": [
            {"id": e.id, "name": e.name, "category": e.category} for e in guide.expertises
        ],
        "tour_types": [{"id": t.id, "name": t.name} for t in guide.tour_types],
    }
    if guide.availability_pattern:
        p = guide.availability_pattern
        result["availability_pattern"] = {
            "id": p.id,
            "timezone": p.timezone,
            "slots": [
                {
                    "id": s.id,
                    "day_of_week": s.day_of_week,
                    "start_time": s.start_time.strftime("%H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                }
                for s in p.slots
            ],
            "exceptions": [
                {
                    "id": e.id,
                    "date": e.date.isoformat(),
                    "type": e.type,
                    "reason": e.reason,
                }
                for e in p.exceptions
            ],
        }
    else:
        result["availability_pattern"] = None
    return result
