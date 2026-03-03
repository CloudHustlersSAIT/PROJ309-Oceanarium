"""Issue routes -- endpoint for reporting issues.

The ``IssueCreate`` Pydantic schema lives here temporarily until Phase 3
extracts it to a dedicated ``schemas/`` layer.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import get_db
from ..services import issue as issue_service


class IssueCreate(BaseModel):
    """Request body for reporting a new issue."""

    description: str


router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("")
def create_issue(issue: IssueCreate, conn=Depends(get_db)):
    """Create a new issue record from the provided description."""
    try:
        return issue_service.create_issue(conn, issue)
    except Exception as e:
        return {"status": "error", "detail": str(e)}
