from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from ..db import engine

router = APIRouter(prefix="/issues", tags=["Issues"])


class IssueCreate(BaseModel):
    description: str


@router.post("")
def create_issue(issue: IssueCreate):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO issues (description)
                    VALUES (:description)
                    RETURNING *
                """),
                {"description": issue.description},
            )
            connection.commit()
            columns = result.keys()
            row = result.fetchone()
            return dict(zip(columns, row))
    except Exception as e:
        return {"status": "error", "detail": str(e)}
