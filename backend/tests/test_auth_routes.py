from unittest.mock import patch

import pytest

from app.services.exceptions import NotFoundError, ValidationError


@pytest.mark.asyncio
async def test_auth_me_success(client):
    with (
        patch("app.routes.auth.engine"),
        patch("app.routes.auth.auth_service") as mock_svc,
    ):
        mock_svc.resolve_authenticated_user.return_value = {
            "uid": "u1",
            "email": "admin@test.com",
            "role": "admin",
            "user_id": 1,
            "guide_id": None,
        }
        response = await client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_auth_me_validation_error(client):
    with (
        patch("app.routes.auth.engine"),
        patch("app.routes.auth.auth_service") as mock_svc,
    ):
        mock_svc.resolve_authenticated_user.side_effect = ValidationError("email missing")
        response = await client.get("/auth/me")

    assert response.status_code == 400
    assert "email missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_me_not_found(client):
    with (
        patch("app.routes.auth.engine"),
        patch("app.routes.auth.auth_service") as mock_svc,
    ):
        mock_svc.resolve_authenticated_user.side_effect = NotFoundError("not mapped")
        response = await client.get("/auth/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_auth_me_db_error(client):
    from sqlalchemy.exc import SQLAlchemyError

    with (
        patch("app.routes.auth.engine"),
        patch("app.routes.auth.auth_service") as mock_svc,
    ):
        mock_svc.resolve_authenticated_user.side_effect = SQLAlchemyError("DB error")
        response = await client.get("/auth/me")

    assert response.status_code == 500
