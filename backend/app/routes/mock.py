"""Mock poller route -- trigger a test-data generation run.

This endpoint wraps the mock poller service in a database transaction.
On success, the transaction auto-commits (via ``engine.begin()``).
On ``SQLAlchemyError``, it attempts to mark the run as FAILED in a
separate transaction before returning HTTP 500.

Note: This route imports ``engine`` directly (the only route that does)
because it needs ``engine.begin()`` for transaction management and a
second connection for the failure-fallback write.  All other routes use
``Depends(get_db)`` exclusively.
"""

from typing import Optional

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
    """Execute one cycle of the mock poller: generate records, insert into staging.

    On success returns a ``MockRunResponse`` summary.  On validation error
    returns 400.  On database error returns 500 and attempts to mark the
    run as FAILED.
    """
    run_id: Optional[str] = None

    try:
        with engine.begin() as conn:
            response = run_mock_poller_service(conn, req)
            run_id = response.run_id
        return response

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)

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
        )
