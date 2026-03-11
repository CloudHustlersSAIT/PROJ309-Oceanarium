import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import get_db
from ..services import issue as issue_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)


class IssueCreate(BaseModel):
    description: str


router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("")
def create_issue(issue: IssueCreate, conn=Depends(get_db)):
    try:
        return issue_service.create_issue(conn, issue)
    except Exception as e:
        return handle_domain_exception(e)