"""Tests for Guide Profile Availability API (GET/PATCH /guide/profile/availability)."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.services.exceptions import NotFoundError, ValidationError


@pytest.mark.asyncio
async def test_get_availability_success(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.get_guide_availability") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.return_value = {"timezone": "UTC", "slots": [{"day": "Monday", "start": "09:00", "end": "17:00"}]}

        response = await client.get("/guide/profile/availability", params={"guide_id": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "UTC"
    assert len(data["slots"]) == 1
    assert data["slots"][0]["day"] == "Monday"
    assert data["slots"][0]["start"] == "09:00"
    mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_availability_empty_slots(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.get_guide_availability") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.return_value = {"timezone": "UTC", "slots": []}

        response = await client.get("/guide/profile/availability", params={"guide_id": 1})

    assert response.status_code == 200
    assert response.json()["slots"] == []


@pytest.mark.asyncio
async def test_get_availability_guide_not_found(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.get_guide_availability") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.side_effect = NotFoundError("Guide not found")

        response = await client.get("/guide/profile/availability", params={"guide_id": 99999})

    assert response.status_code == 404
    assert "Guide not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_availability_db_unavailable(client):
    with patch("app.routes.guide_availability.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.side_effect = OperationalError("", "", None)

        response = await client.get("/guide/profile/availability", params={"guide_id": 1})

    assert response.status_code == 503
    assert "Database unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_availability_missing_guide_id(client):
    response = await client.get("/guide/profile/availability")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_availability_success(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.update_guide_availability") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.return_value = None

        response = await client.patch(
            "/guide/profile/availability",
            params={"guide_id": 1},
            json={"slots": [{"day": "Monday", "start": "09:00", "end": "17:00"}]},
        )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "updated" in response.json()["message"].lower()
    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_patch_availability_guide_not_found(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.update_guide_availability") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.side_effect = NotFoundError("Guide not found")

        response = await client.patch(
            "/guide/profile/availability",
            params={"guide_id": 99999},
            json={"slots": [{"day": "Monday", "start": "09:00", "end": "17:00"}]},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_availability_validation_error(client):
    with (
        patch("app.routes.guide_availability.engine.connect") as mock_connect,
        patch("app.routes.guide_availability.availability_service.update_guide_availability") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.side_effect = ValidationError("start time must be before end time")

        response = await client.patch(
            "/guide/profile/availability",
            params={"guide_id": 1},
            json={"slots": [{"day": "Monday", "start": "17:00", "end": "09:00"}]},
        )

    assert response.status_code == 400
    assert "start time" in response.json()["detail"].lower() or "before" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_patch_availability_db_unavailable(client):
    with patch("app.routes.guide_availability.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.side_effect = OperationalError("", "", None)

        response = await client.patch(
            "/guide/profile/availability",
            params={"guide_id": 1},
            json={"slots": [{"day": "Monday", "start": "09:00", "end": "17:00"}]},
        )

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_patch_availability_missing_guide_id(client):
    response = await client.patch(
        "/guide/profile/availability",
        json={"slots": [{"day": "Monday", "start": "09:00", "end": "17:00"}]},
    )
    assert response.status_code == 422
