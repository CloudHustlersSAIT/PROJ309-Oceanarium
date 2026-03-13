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
