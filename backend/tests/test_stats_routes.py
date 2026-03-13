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


@pytest.mark.asyncio
async def test_get_admin_dashboard_success(client):
    with patch("app.routes.stats.stats_service") as mock_svc:
        mock_svc.get_admin_dashboard.return_value = {
            "filters": {
                "selectedDate": "2026-03-12",
                "period": "this_month",
                "startDate": "2026-03-01",
                "endDate": "2026-03-12",
            },
            "kpis": {
                "totalToursConducted": 8,
                "totalVisitorsServed": 51,
                "avgOccupancyRate": None,
                "avgGuideRating": 4.6,
            },
            "toursPerYear": [],
            "visitorsPerTour": [],
            "toursByLanguage": [],
            "bookingsVsCancellations": [],
            "topRatedGuides": [],
            "meta": {"occupancyRateAvailable": False, "notes": []},
        }
        response = await client.get("/stats/admin-dashboard?selected_date=2026-03-12&period=this_month")

    assert response.status_code == 200
    assert response.json()["kpis"]["totalToursConducted"] == 8
    assert response.json()["filters"]["period"] == "this_month"


@pytest.mark.asyncio
async def test_get_admin_dashboard_internal_error(client):
    with patch("app.routes.stats.stats_service") as mock_svc:
        mock_svc.get_admin_dashboard.side_effect = RuntimeError("fail")
        response = await client.get("/stats/admin-dashboard")

    assert response.status_code == 500
