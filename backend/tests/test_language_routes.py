from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_languages_success(client):
    with patch("app.routes.language.language_service") as mock_svc:
        mock_svc.list_languages.return_value = [
            {"id": 1, "code": "en", "name": "English"},
        ]
        response = await client.get("/languages")

    assert response.status_code == 200
    assert response.json()[0]["code"] == "en"


@pytest.mark.asyncio
async def test_get_languages_internal_error(client):
    with patch("app.routes.language.language_service") as mock_svc:
        mock_svc.list_languages.side_effect = RuntimeError("DB down")
        response = await client.get("/languages")

    assert response.status_code == 500
