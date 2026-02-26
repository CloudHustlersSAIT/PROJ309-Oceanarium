from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.survey import Survey
from ..schemas.survey import SurveyCreate, SurveyUpdate

router = APIRouter(prefix="/surveys", tags=["Surveys"])


@router.get("")
def list_surveys(db: Session = Depends(get_db)):
    return [_survey_to_dict(s) for s in db.query(Survey).all()]


@router.get("/{survey_id}")
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return _survey_to_dict(survey)


@router.post("", status_code=201)
def create_survey(payload: SurveyCreate, db: Session = Depends(get_db)):
    survey = Survey(
        customer_id=payload.customer_id,
        guide_id=payload.guide_id,
        booking_version_id=payload.booking_version_id,
        comment=payload.comment,
        rating=payload.rating,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return _survey_to_dict(survey)


@router.patch("/{survey_id}")
def update_survey(survey_id: int, payload: SurveyUpdate, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if payload.comment is not None:
        survey.comment = payload.comment
    if payload.rating is not None:
        survey.rating = payload.rating

    db.commit()
    db.refresh(survey)
    return _survey_to_dict(survey)


@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: int, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    db.delete(survey)
    db.commit()


def _survey_to_dict(survey: Survey) -> dict:
    return {
        "id": survey.id,
        "customer_id": survey.customer_id,
        "guide_id": survey.guide_id,
        "booking_version_id": survey.booking_version_id,
        "comment": survey.comment,
        "rating": survey.rating,
    }
