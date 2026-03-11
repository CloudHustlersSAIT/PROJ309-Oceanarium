from __future__ import annotations

import ipaddress
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

router = APIRouter(prefix="/mock", tags=["Mock Poller"])


def _is_loopback_ip(ip_value: str | None) -> bool:
    if not ip_value:
        return False

    candidate = ip_value.strip().strip('"').strip("[]")
    if not candidate:
        return False

    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _get_originating_ip(request: Request) -> str | None:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",", 1)[0].strip()

    forwarded = request.headers.get("forwarded")
    if forwarded:
        for part in forwarded.split(";"):
            key, _, value = part.strip().partition("=")
            if key.lower() == "for" and value:
                return value.strip()

    return request.client.host if request.client else None


def _require_dev_or_localhost(request: Request) -> None:
    """Allow the mock poller in development mode or from localhost (EC2 cronjob)."""
    if ENV == "development":
        return

    client_ip = _get_originating_ip(request)
    if _is_loopback_ip(client_ip):
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
