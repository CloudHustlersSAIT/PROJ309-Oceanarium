from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_notifications_success(client):
    with patch("app.routes.notification.notification_service") as mock_svc:
        mock_svc.list_notifications.return_value = [{"id": 1, "message": "Hello"}]
        response = await client.get("/notifications")

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_notifications_internal_error(client):
    with patch("app.routes.notification.notification_service") as mock_svc:
        mock_svc.list_notifications.side_effect = RuntimeError("fail")
        response = await client.get("/notifications")

    assert response.status_code == 500
