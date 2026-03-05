import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..services import issue as issue_service

logger = logging.getLogger(__name__)


class IssueCreate(BaseModel):
    description: str


router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("")
def create_issue(issue: IssueCreate, conn=Depends(get_db)):
    try:
        return issue_service.create_issue(conn, issue)
    except Exception:
        logger.exception("Unexpected error creating issue")
        raise HTTPException(status_code=500, detail="Internal server error")
