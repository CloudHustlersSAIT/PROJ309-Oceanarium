from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.issue import Issue

router = APIRouter(prefix="/issues", tags=["Issues"])


class IssueCreate(BaseModel):
    description: str


@router.post("", status_code=201)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db)):
    issue = Issue(description=payload.description)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return {
        "id": issue.id,
        "description": issue.description,
        "created_at": issue.created_at.isoformat() if issue.created_at else None,
    }
