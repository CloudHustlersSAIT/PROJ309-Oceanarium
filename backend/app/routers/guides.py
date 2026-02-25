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
from ..schemas.guide import (
    AvailabilitySetIn,
    GuideCreate,
    GuideOut,
    GuideUpdate,
)

router = APIRouter(prefix="/guides", tags=["Guides"])


@router.get("", response_model=list)
def list_guides(db: Session = Depends(get_db)):
    guides = db.query(Guide).all()
    return [_guide_to_dict(g) for g in guides]


@router.post("", status_code=201)
def create_guide(payload: GuideCreate, db: Session = Depends(get_db)):
    guide = Guide(name=payload.name, email=payload.email, is_active=payload.is_active)
    db.add(guide)
    db.flush()

    for code in payload.languages:
        lang = db.query(Language).filter(Language.code == code).first()
        if not lang:
            lang = Language(code=code, name=code)
            db.add(lang)
            db.flush()
        guide.languages.append(lang)

    for exp_name in payload.expertises:
        exp = db.query(Expertise).filter(Expertise.name == exp_name).first()
        if not exp:
            exp = Expertise(name=exp_name, category="General")
            db.add(exp)
            db.flush()
        guide.expertises.append(exp)

    db.commit()
    db.refresh(guide)
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

    if payload.name is not None:
        guide.name = payload.name
    if payload.email is not None:
        guide.email = payload.email
    if payload.is_active is not None:
        guide.is_active = payload.is_active

    if payload.languages is not None:
        guide.languages.clear()
        for code in payload.languages:
            lang = db.query(Language).filter(Language.code == code).first()
            if not lang:
                lang = Language(code=code, name=code)
                db.add(lang)
                db.flush()
            guide.languages.append(lang)

    if payload.expertises is not None:
        guide.expertises.clear()
        for exp_name in payload.expertises:
            exp = db.query(Expertise).filter(Expertise.name == exp_name).first()
            if not exp:
                exp = Expertise(name=exp_name, category="General")
                db.add(exp)
                db.flush()
            guide.expertises.append(exp)

    db.commit()
    db.refresh(guide)
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
    return _guide_to_dict(guide)


def _guide_to_dict(guide: Guide) -> dict:
    result = {
        "id": guide.id,
        "name": guide.name,
        "email": guide.email,
        "is_active": guide.is_active,
        "languages": [{"id": l.id, "code": l.code, "name": l.name} for l in guide.languages],
        "expertises": [
            {"id": e.id, "name": e.name, "category": e.category} for e in guide.expertises
        ],
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
