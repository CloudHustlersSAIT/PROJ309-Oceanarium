from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_guides_success(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.list_guides.return_value = [
            {"id": 1, "first_name": "Maria", "last_name": "Silva"},
            {"id": 2, "first_name": "João", "last_name": "Costa"},
        ]
        response = await client.get("/guides")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["first_name"] == "Maria"


@pytest.mark.asyncio
async def test_get_guides_internal_error(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.list_guides.side_effect = RuntimeError("DB error")
        response = await client.get("/guides")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]
