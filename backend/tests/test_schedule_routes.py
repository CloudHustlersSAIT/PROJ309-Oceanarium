from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_schedules_success(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.list_schedules.return_value = [
            {"id": 1, "tour_name": "Ocean Walk", "status": "CONFIRMED"},
        ]
        response = await client.get("/schedules")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tour_name"] == "Ocean Walk"


@pytest.mark.asyncio
async def test_get_schedules_with_query_params(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.list_schedules.return_value = []
        response = await client.get("/schedules?start_date=2026-01-01&status=CONFIRMED")

    assert response.status_code == 200
    mock_svc.list_schedules.assert_called_once()


@pytest.mark.asyncio
async def test_get_schedules_validation_error(client):
    from app.services.exceptions import ValidationError

    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.list_schedules.side_effect = ValidationError("Invalid range")
        response = await client.get("/schedules?start_date=2026-03-10&end_date=2026-03-01")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_schedule_success(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.create_schedule.return_value = {"id": 1, "status": "CONFIRMED"}
        response = await client.post(
            "/schedules",
            json={
                "tour_id": 1,
                "language_code": "en",
                "event_start_datetime": "2026-03-10T10:00:00",
                "event_end_datetime": "2026-03-10T11:00:00",
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_schedules_internal_error(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.list_schedules.side_effect = RuntimeError("DB crash")
        response = await client.get("/schedules")

    assert response.status_code == 500
