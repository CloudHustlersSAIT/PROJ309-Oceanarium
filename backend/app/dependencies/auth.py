import os

from fastapi import Header, HTTPException
from ..firebase_auth import verify_firebase_token

ENV = os.getenv("ENV", "development").lower()

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

    In development mode, allows a local bypass if no Authorization header is provided.
    This keeps local teammate testing simple while protecting deployed environments.
    """
    if ENV == "development" and not authorization:
        return {
            "uid": "local-dev-user",
            "email": "local-dev@oceanarium.local",
            "auth_mode": "development-bypass",
        }

    bearer_token = _extract_bearer_token(authorization)
    decoded = verify_firebase_token(bearer_token)
    return decoded