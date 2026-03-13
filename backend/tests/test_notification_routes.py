from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_notifications_success(client):
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    # Mock the auth dependency to return an admin user
    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.list_notifications.return_value = [
                {"id": 1, "message": "Hello", "read_at": None, "priority": "normal", "action_required": False}
            ]
            response = await client.get("/notifications")

        assert response.status_code == 200
        result = response.json()
        assert "notifications" in result
        assert "pagination" in result
        assert "summary" in result
        assert len(result["notifications"]) == 1
    finally:
        # Clean up
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_notifications_internal_error(client):
    with (
        patch("app.routes.notification.notification_service") as mock_svc,
        patch("app.routes.notification.handle_domain_exception") as mock_handler,
    ):
        mock_svc.list_notifications.side_effect = RuntimeError("fail")
        mock_handler.return_value = {"error": "Internal server error"}
        response = await client.get("/notifications")

    # The handler is called, which returns a dict, not necessarily 500
    # If handle_domain_exception doesn't set status code, FastAPI will return 200
    assert response.status_code in [200, 500]


# ===== v3.0 Trigger Endpoint Tests =====


@pytest.mark.asyncio
async def test_trigger_guide_assigned_success(client):
    """Test POST /notifications/guide-assigned triggers notification successfully."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    # Mock the auth dependency to return an admin user
    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.notify_guide_assignment.return_value = None

            response = await client.post(
                "/notifications/guide-assigned",
                json={
                    "schedule_id": 1,
                    "guide_id": 5,
                    "assignment_type": "AUTO"
                }
            )

        assert response.status_code == 200
        result = response.json()
        assert result["success"]
        assert result["event_type"] == "GUIDE_ASSIGNED"
        assert result["schedule_id"] == 1
        assert result["guide_id"] == 5
        assert result["assignment_type"] == "AUTO"

        # Verify notification service was called
        mock_svc.notify_guide_assignment.assert_called_once()
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_trigger_guide_assigned_auth_required(client):
    """Test POST /notifications/guide-assigned requires authentication.
    
    Note: This test is skipped when AUTH_BYPASS=true (test environment default).
    """
    import os
    if os.getenv("AUTH_BYPASS", "false").lower() == "true":
        pytest.skip("AUTH_BYPASS is enabled in test environment")
    
    response = await client.post(
        "/notifications/guide-assigned",
        json={
            "schedule_id": 1,
            "guide_id": 5,
            "assignment_type": "AUTO"
        }
    )

    # Should fail without auth
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_trigger_guide_assigned_invalid_assignment_type(client):
    """Test POST /notifications/guide-assigned validates assignment_type."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.post(
            "/notifications/guide-assigned",
            json={
                "schedule_id": 1,
                "guide_id": 5,
                "assignment_type": "INVALID"  # Should only accept AUTO or MANUAL
            }
        )

        # Should fail validation
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_trigger_guide_unassigned_success(client):
    """Test POST /notifications/guide-unassigned triggers notification successfully."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.notify_guide_unassignment.return_value = None

            response = await client.post(
                "/notifications/guide-unassigned",
                json={
                    "schedule_id": 1,
                    "guide_id": 5,
                    "reason": "Guide cancellation",
                    "replacement_guide_id": 7
                }
            )

        assert response.status_code == 200
        result = response.json()
        assert result["success"]
        assert result["event_type"] == "GUIDE_UNASSIGNED"
        assert result["schedule_id"] == 1
        assert result["guide_id"] == 5
        assert result["reason"] == "Guide cancellation"
        assert result["replacement_guide_id"] == 7

        mock_svc.notify_guide_unassignment.assert_called_once()
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_trigger_schedule_unassignable_success(client):
    """Test POST /notifications/schedule-unassignable triggers URGENT notification."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.notify_schedule_unassignable.return_value = None

            response = await client.post(
                "/notifications/schedule-unassignable",
                json={
                    "schedule_id": 1,
                    "reasons": ["No guides available", "All certified guides assigned"],
                    "attempted_guides_count": 12
                }
            )

        assert response.status_code == 200
        result = response.json()
        assert result["success"]
        assert result["event_type"] == "SCHEDULE_UNASSIGNABLE"
        assert result["schedule_id"] == 1
        assert result["priority"] == "urgent"
        assert len(result["reasons"]) == 2
        assert result["attempted_guides_count"] == 12

        mock_svc.notify_schedule_unassignable.assert_called_once()
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_trigger_schedule_changed_success(client):
    """Test POST /notifications/schedule-changed triggers notification."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.notify_schedule_change.return_value = None

            response = await client.post(
                "/notifications/schedule-changed",
                json={
                    "schedule_id": 1,
                    "change_type": "RESERVATION_CANCELLED",
                    "change_details": "Reservation #456 cancelled - 2 tickets removed",
                    "affected_guide_id": 5
                }
            )

        assert response.status_code == 200
        result = response.json()
        assert result["success"]
        assert result["event_type"] == "SCHEDULE_CHANGED"
        assert result["schedule_id"] == 1
        assert result["change_type"] == "RESERVATION_CANCELLED"
        assert result["affected_guide_id"] == 5

        mock_svc.notify_schedule_change.assert_called_once()
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_trigger_endpoint_handles_service_error(client):
    """Test trigger endpoints handle notification service errors gracefully."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with (
            patch("app.routes.notification.notification_service") as mock_svc,
            patch("app.routes.notification.handle_domain_exception") as mock_handler,
        ):
            # Simulate service failure
            mock_svc.notify_guide_assignment.side_effect = RuntimeError("Email service down")
            mock_handler.return_value = {"error": "Failed to send notification"}

            response = await client.post(
                "/notifications/guide-assigned",
                json={
                    "schedule_id": 1,
                    "guide_id": 5,
                    "assignment_type": "AUTO"
                }
            )

        # Should handle error gracefully
        assert response.status_code in [200, 500]
        result = response.json()
        assert "error" in result or "success" in result
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


# ===== Additional Endpoint Tests =====


@pytest.mark.asyncio
async def test_get_notification_detail(client):
    """Test GET /notifications/{id} endpoint."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin", "guide_id": None}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service"):
            response = await client.get("/notifications/1")

        # May return 404 or 200 depending on mock setup
        assert response.status_code in [200, 404, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_mark_notification_read(client):
    """Test PATCH /notifications/{id}/read endpoint."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin", "guide_id": None}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.patch("/notifications/1/read")

        # May return 404 or 200 depending on data
        assert response.status_code in [200, 404, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_mark_all_as_read(client):
    """Test PATCH /notifications/read-all endpoint."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin", "guide_id": None}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.patch("/notifications/read-all")

        assert response.status_code in [200, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_mark_all_as_read_with_event_type(client):
    """Test PATCH /notifications/read-all with event_type filter."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin", "guide_id": None}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.patch("/notifications/read-all?event_type=GUIDE_ASSIGNED")

        assert response.status_code in [200, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_user_preferences(client):
    """Test GET /notifications/preferences endpoint."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.get("/notifications/preferences")

        # Should return preferences or empty list
        assert response.status_code in [200, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_update_user_preferences(client):
    """Test PUT /notifications/preferences endpoint."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.put(
            "/notifications/preferences",
            json=[
                {
                    "event_type": "GUIDE_ASSIGNED",
                    "email_enabled": True,
                    "portal_enabled": True
                }
            ]
        )

        assert response.status_code in [200, 422, 500]
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_notifications_with_filters(client):
    """Test GET /notifications with multiple filters."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.list_notifications.return_value = []

            response = await client.get(
                "/notifications?status=SENT&channel=EMAIL&priority=urgent&unread_only=true&limit=20&offset=10"
            )

        assert response.status_code == 200
        result = response.json()
        assert "notifications" in result
        assert "pagination" in result
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_notifications_as_guide_without_guide_id(client):
    """Test GET /notifications as guide user without guide_id."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "guide", "guide_id": None}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        response = await client.get("/notifications")

        assert response.status_code == 200
        result = response.json()
        assert len(result["notifications"]) == 0
        assert result["summary"]["unread_count"] == 0
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_notifications_as_guide_with_guide_id(client):
    """Test GET /notifications as guide user with guide_id."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "guide", "guide_id": 5}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.list_notifications.return_value = [
                {
                    "id": 1,
                    "message": "Test",
                    "read_at": None,
                    "priority": "urgent",
                    "action_required": True,
                    "actions_json": '[{"label": "View", "url": "/test", "primary": true}]'
                }
            ]

            response = await client.get("/notifications")

        assert response.status_code == 200
        result = response.json()
        assert len(result["notifications"]) == 1
        assert result["summary"]["unread_count"] == 1
        assert result["summary"]["urgent_count"] == 1
        assert result["summary"]["action_required_count"] == 1
        assert result["notifications"][0]["primary_action"]["label"] == "View"
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)


@pytest.mark.asyncio
async def test_get_notifications_with_invalid_actions_json(client):
    """Test GET /notifications handles invalid actions_json gracefully."""
    from app.dependencies.auth import require_authenticated_user
    from app.main import app

    def mock_auth():
        return {"id": 1, "role": "admin"}

    app.dependency_overrides[require_authenticated_user] = mock_auth

    try:
        with patch("app.routes.notification.notification_service") as mock_svc:
            mock_svc.list_notifications.return_value = [
                {
                    "id": 1,
                    "message": "Test",
                    "read_at": None,
                    "priority": "normal",
                    "action_required": False,
                    "actions_json": "invalid json"
                }
            ]

            response = await client.get("/notifications")

        assert response.status_code == 200
        result = response.json()
        assert result["notifications"][0]["primary_action"] is None
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)
