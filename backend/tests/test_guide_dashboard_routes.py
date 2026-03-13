from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_dashboard_success(client):
    with (
        patch("app.routes.guide_dashboard.engine"),
        patch("app.routes.guide_dashboard.dashboard_service") as mock_svc,
    ):
        mock_svc.get_dashboard.return_value = {
            "next_tour": None,
            "tours_this_week": 2,
            "pending_requests": 0,
            "rating": 4.5,
            "today_schedule": [],
        }
        response = await client.get("/guide/dashboard", params={"guide_id": 5})

    assert response.status_code == 200
    assert response.json()["tours_this_week"] == 2


@pytest.mark.asyncio
async def test_dashboard_internal_error(client):
    with (
        patch("app.routes.guide_dashboard.engine"),
        patch("app.routes.guide_dashboard.dashboard_service") as mock_svc,
    ):
        mock_svc.get_dashboard.side_effect = RuntimeError("DB down")
        response = await client.get("/guide/dashboard", params={"guide_id": 5})

    assert response.status_code == 200
    assert response.json()["error"] == "Internal server error"
