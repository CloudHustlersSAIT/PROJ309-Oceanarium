from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from ..db import engine
from ..services.exceptions import ValidationError
from ..services.mock_poller import (
    MockRunRequest,
    MockRunResponse,
    finalize_run_failure,
    run_mock_poller_service,
)

ENV = os.getenv("ENV", "production").lower()
_LOOPBACK = {"127.0.0.1", "::1"}

router = APIRouter(prefix="/mock", tags=["Mock Poller"])


def _require_dev_or_localhost(request: Request) -> None:
    """Allow the mock poller in development mode or from localhost (EC2 cronjob)."""
    if ENV == "development":
        return
    client_ip = request.client.host if request.client else None
    if client_ip in _LOOPBACK:
        return
    raise HTTPException(
        status_code=403,
        detail="Mock poller is only available in development or from localhost",
    )


@router.post("/run", response_model=MockRunResponse)
def run_mock_poller(
    req: MockRunRequest,
    _guard: None = Depends(_require_dev_or_localhost),
) -> MockRunResponse:
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
