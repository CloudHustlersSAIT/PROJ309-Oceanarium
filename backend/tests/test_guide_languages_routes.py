"""Tests for Guide Profile Languages API (GET/PATCH /guide/profile/languages)."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.services.exceptions import NotFoundError, ValidationError


@pytest.mark.asyncio
async def test_get_languages_success(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.get_guide_languages") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.return_value = {
            "languages": [{"id": 1, "name": "English", "code": "en"}, {"id": 2, "name": "French", "code": "fr"}],
        }

        response = await client.get("/guide/profile/languages", params={"guide_id": 1})

    assert response.status_code == 200
    data = response.json()
    assert len(data["languages"]) == 2
    assert data["languages"][0]["id"] == 1 and data["languages"][0]["code"] == "en"
    mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_languages_empty(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.get_guide_languages") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.return_value = {"languages": []}

        response = await client.get("/guide/profile/languages", params={"guide_id": 1})

    assert response.status_code == 200
    assert response.json()["languages"] == []


@pytest.mark.asyncio
async def test_get_languages_guide_not_found(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.get_guide_languages") as mock_get,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_get.side_effect = NotFoundError("Guide not found")

        response = await client.get("/guide/profile/languages", params={"guide_id": 99999})

    assert response.status_code == 404
    assert "Guide not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_languages_db_unavailable(client):
    with patch("app.routes.guide_languages.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.side_effect = OperationalError("", "", None)

        response = await client.get("/guide/profile/languages", params={"guide_id": 1})

    assert response.status_code == 503
    assert "Database unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_languages_missing_guide_id(client):
    response = await client.get("/guide/profile/languages")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_languages_success(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.update_guide_languages") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.return_value = None

        response = await client.patch(
            "/guide/profile/languages",
            params={"guide_id": 1},
            json={"language_ids": [1, 2]},
        )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "updated" in response.json()["message"].lower()
    mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_patch_languages_clear_all(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.update_guide_languages") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None

        response = await client.patch(
            "/guide/profile/languages",
            params={"guide_id": 1},
            json={"language_ids": []},
        )

    assert response.status_code == 200
    mock_update.assert_called_once()
    call_args = mock_update.call_args[0]
    assert call_args[1] == 1  # guide_id
    assert call_args[2] == []  # language_ids


@pytest.mark.asyncio
async def test_patch_languages_guide_not_found(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.update_guide_languages") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.side_effect = NotFoundError("Guide not found")

        response = await client.patch(
            "/guide/profile/languages",
            params={"guide_id": 99999},
            json={"language_ids": [1]},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_languages_invalid_language_id(client):
    with (
        patch("app.routes.guide_languages.engine.connect") as mock_connect,
        patch("app.routes.guide_languages.language_service.update_guide_languages") as mock_update,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_connect.return_value.__exit__.return_value = None
        mock_update.side_effect = ValidationError("Language id 99999 not found in languages table")

        response = await client.patch(
            "/guide/profile/languages",
            params={"guide_id": 1},
            json={"language_ids": [1, 99999]},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_languages_db_unavailable(client):
    with patch("app.routes.guide_languages.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.side_effect = OperationalError("", "", None)

        response = await client.patch(
            "/guide/profile/languages",
            params={"guide_id": 1},
            json={"language_ids": [1]},
        )

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_patch_languages_missing_guide_id(client):
    response = await client.patch("/guide/profile/languages", json={"language_ids": [1]})
    assert response.status_code == 422
