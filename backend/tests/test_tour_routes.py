from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_tours_success(client):
    with patch("app.routes.tour.tour_service") as mock_svc:
        mock_svc.list_tours.return_value = [
            {"id": 1, "name": "Ocean Walk"},
            {"id": 2, "name": "Reef Dive"},
        ]
        response = await client.get("/tours")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_tours_internal_error(client):
    with patch("app.routes.tour.tour_service") as mock_svc:
        mock_svc.list_tours.side_effect = RuntimeError("DB error")
        response = await client.get("/tours")

    assert response.status_code == 500
