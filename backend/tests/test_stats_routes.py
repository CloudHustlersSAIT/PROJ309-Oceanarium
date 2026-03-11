from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_stats_success(client):
    with patch("app.routes.stats.stats_service") as mock_svc:
        mock_svc.get_stats.return_value = {"total_tours": 5, "total_guides": 3}
        response = await client.get("/stats")

    assert response.status_code == 200
    assert response.json()["total_tours"] == 5


@pytest.mark.asyncio
async def test_get_stats_internal_error(client):
    with patch("app.routes.stats.stats_service") as mock_svc:
        mock_svc.get_stats.side_effect = RuntimeError("fail")
        response = await client.get("/stats")

    assert response.status_code == 500
