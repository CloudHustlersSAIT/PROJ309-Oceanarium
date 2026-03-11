from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_health_db_success(client):
    with patch("app.routes.health.test_connection") as mock_tc:
        mock_tc.return_value = 1
        response = await client.get("/health/db")

    assert response.status_code == 200
    assert response.json()["db_check"] == 1


@pytest.mark.asyncio
async def test_health_db_unavailable(client):
    with patch("app.routes.health.test_connection") as mock_tc:
        mock_tc.return_value = None
        response = await client.get("/health/db")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_health_db_exception(client):
    with patch("app.routes.health.test_connection") as mock_tc:
        mock_tc.side_effect = RuntimeError("connection failed")
        response = await client.get("/health/db")

    assert response.status_code == 500
