from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from ..db import engine
from ..services.exceptions import ValidationError
from ..services.mock_poller import (
    MockRunRequest,
    MockRunResponse,
    finalize_run_failure,
    run_mock_poller_service,
)

router = APIRouter(prefix="/mock", tags=["Mock Poller"])


@router.post("/run", response_model=MockRunResponse)
def run_mock_poller(req: MockRunRequest) -> MockRunResponse:
    run_id: int | None = None

    try:
        with engine.begin() as conn:
            response = run_mock_poller_service(conn, req)
            run_id = response.run_id
        return response

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message) from e

    except SQLAlchemyError as e:
        if run_id:
            try:
                with engine.begin() as conn:
                    finalize_run_failure(conn, run_id=run_id, error_message=str(e))
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail="Mock poller execution failed. Check server logs.",
        ) from e
