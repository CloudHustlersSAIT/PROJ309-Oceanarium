from __future__ import annotations

import os

from fastapi import Header, HTTPException

from ..firebase_auth import verify_firebase_token


def _is_development_bypass_enabled() -> bool:
    env = os.getenv("ENV", "production").lower()
    auth_bypass = os.getenv("AUTH_BYPASS", "false").lower() == "true"
    return env == "development" and auth_bypass


def _build_development_bypass_claims(email_override: str | None = None) -> dict:
    email = str(email_override or os.getenv("AUTH_BYPASS_EMAIL", "local-dev@oceanarium.local")).strip().lower()
    return {
        "uid": os.getenv("AUTH_BYPASS_UID", "local-dev-user"),
        "email": email,
        "auth_mode": "development-bypass",
    }


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
    x_dev_bypass_email: str | None = Header(default=None),
) -> dict:
    """
    Returns decoded Firebase claims for an authenticated user.

    A local bypass is only active when ENV=development AND AUTH_BYPASS=true are both
    explicitly set, preventing accidental bypasses from misconfigured environments.
    """
    bypass_enabled = _is_development_bypass_enabled()

    if bypass_enabled and not authorization:
        return _build_development_bypass_claims(x_dev_bypass_email)

    bearer_token = _extract_bearer_token(authorization)

    try:
        decoded = verify_firebase_token(bearer_token)
        return decoded
    except HTTPException:
        if bypass_enabled:
            return _build_development_bypass_claims(x_dev_bypass_email)
        raise
