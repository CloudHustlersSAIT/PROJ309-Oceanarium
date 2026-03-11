from __future__ import annotations

import os

from fastapi import Header, HTTPException

from ..firebase_auth import verify_firebase_token

# Default to production to ensure the safest behavior when ENV is not explicitly set.
ENV = os.getenv("ENV", "production").lower()
# Bypass auth only when explicitly opted in (AUTH_BYPASS=true) AND in development mode.
AUTH_BYPASS = os.getenv("AUTH_BYPASS", "false").lower() == "true"


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must start with 'Bearer '",
        )

    bearer_token = authorization.removeprefix("Bearer ").strip()
    if not bearer_token:
        raise HTTPException(
            status_code=401,
            detail="Bearer token is missing",
        )

    return bearer_token


def require_authenticated_user(
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Returns decoded Firebase claims for an authenticated user.

    A local bypass is only active when ENV=development AND AUTH_BYPASS=true are both
    explicitly set, preventing accidental bypasses from misconfigured environments.
    """
    if ENV == "development" and AUTH_BYPASS and not authorization:
        return {
            "uid": "local-dev-user",
            "email": "local-dev@oceanarium.local",
            "auth_mode": "development-bypass",
        }

    bearer_token = _extract_bearer_token(authorization)
    decoded = verify_firebase_token(bearer_token)
    return decoded
