from unittest.mock import patch

import pytest

from app.services.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_cancel_guide_success(client):
    with patch("app.routes.schedule.rescheduling_service") as mock_svc:
        mock_svc.handle_guide_cancellation_and_notify.return_value = {
            "schedule_id": 1,
            "old_guide_id": 5,
            "new_guide_id": 7,
            "new_guide_name": "Carlos Santos",
            "status": "ASSIGNED",
        }
        response = await client.delete("/schedules/1/guide")

    assert response.status_code == 200
    data = response.json()
    assert data["old_guide_id"] == 5
    assert data["new_guide_id"] == 7


@pytest.mark.asyncio
async def test_cancel_guide_not_found(client):
    with patch("app.routes.schedule.rescheduling_service") as mock_svc:
        mock_svc.handle_guide_cancellation_and_notify.side_effect = NotFoundError("Schedule not found")
        response = await client.delete("/schedules/999/guide")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_guide_internal_error(client):
    with patch("app.routes.schedule.rescheduling_service") as mock_svc:
        mock_svc.handle_guide_cancellation_and_notify.side_effect = RuntimeError("unexpected")
        response = await client.delete("/schedules/1/guide")

    assert response.status_code == 500
