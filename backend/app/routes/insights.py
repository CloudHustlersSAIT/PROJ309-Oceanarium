from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services.content_moderation import assert_text_is_safe
from ..services.exceptions import ValidationError
from ..services.insights import run_insight_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["Insights"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class InsightRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartData(BaseModel):
    type: str
    title: str
    data: list[ChartDataPoint]


class Recommendation(BaseModel):
    title: str
    description: str
    action_type: str


class InsightResponse(BaseModel):
    question: str
    answer: str
    chart: ChartData | None = None
    recommendations: list[Recommendation] = []
    sql_used: str = ""


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/query", response_model=InsightResponse)
def query_insights(
    payload: InsightRequest,
    conn=Depends(get_db),
    _user: dict = Depends(require_authenticated_user),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=422,
            detail={"code": "EMPTY_QUESTION", "message": "Question cannot be empty"},
        )

    # Content safety check — runs before any LLM call
    try:
        assert_text_is_safe(question, "question")
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "CONTENT_SAFETY_BLOCKED", "message": exc.message},
        ) from exc

    # Two-phase LLM + DB flow
    try:
        result = run_insight_query(conn, question)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "UNSAFE_SQL", "message": exc.message},
        ) from exc
    except OpenAIError as exc:
        logger.error("OpenAI error during insights query: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "OPENAI_UNAVAILABLE",
                "message": "AI service is temporarily unavailable. Please try again later.",
            },
        ) from exc
    except RuntimeError as exc:
        logger.error("Insights query runtime error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_ERROR", "message": str(exc)},
        ) from exc

    return result
