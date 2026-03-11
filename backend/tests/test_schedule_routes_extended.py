from unittest.mock import patch

import pytest

from app.services.exceptions import ConflictError, NotFoundError


@pytest.mark.asyncio
async def test_create_schedule_not_found(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.create_schedule.side_effect = NotFoundError("Tour not found")
        response = await client.post(
            "/schedules",
            json={
                "tour_id": 999,
                "language_code": "en",
                "event_start_datetime": "2026-03-10T10:00:00",
                "event_end_datetime": "2026-03-10T11:00:00",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_schedule_conflict(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.create_schedule.side_effect = ConflictError("Conflict")
        response = await client.post(
            "/schedules",
            json={
                "tour_id": 1,
                "language_code": "en",
                "event_start_datetime": "2026-03-10T10:00:00",
                "event_end_datetime": "2026-03-10T11:00:00",
            },
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_schedule_internal_error(client):
    with patch("app.routes.schedule.schedule_service") as mock_svc:
        mock_svc.create_schedule.side_effect = RuntimeError("crash")
        response = await client.post(
            "/schedules",
            json={
                "tour_id": 1,
                "language_code": "en",
                "event_start_datetime": "2026-03-10T10:00:00",
                "event_end_datetime": "2026-03-10T11:00:00",
            },
        )

    assert response.status_code == 500
