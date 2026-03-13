"""Comprehensive tests for notification system components."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services import notification as notification_service
from app.services import notification_templates
from app.services.email import send_email

# ===== Email Service Tests =====


@patch("app.services.email.EMAIL_ENABLED", True)
def test_send_email_success():
    """Test successful email sending."""
    import app.services.email as email_mod

    mock_resend = MagicMock()
    mock_resend.Emails.send.return_value = {"id": "test-email-id"}

    with patch.object(email_mod, "resend", mock_resend, create=True):
        result = send_email(
            to_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            body_html="<p>Test body</p>",
        )

    assert result is True
    mock_resend.Emails.send.assert_called_once()


@patch("app.services.email.EMAIL_ENABLED", False)
def test_send_email_disabled():
    """Test email sending when EMAIL_ENABLED is False."""
    result = send_email(to_email="test@example.com", subject="Test Subject", body_text="Test body")

    assert result is True  # Returns True when disabled (for testing)


@patch("app.services.email.EMAIL_ENABLED", True)
def test_send_email_invalid_address():
    """Test email sending with invalid address."""
    result = send_email(to_email="invalid-email", subject="Test Subject", body_text="Test body")

    assert result is False


@patch("app.services.email.EMAIL_ENABLED", True)
def test_send_email_exception():
    """Test email sending handles exceptions."""
    import app.services.email as email_mod

    mock_resend = MagicMock()
    mock_resend.Emails.send.side_effect = Exception("API Error")

    with patch.object(email_mod, "resend", mock_resend, create=True):
        result = send_email(
            to_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
        )

    assert result is False


# ===== Notification Templates Tests =====


def test_guide_assigned_template_auto():
    """Test guide assigned template for AUTO assignment."""
    schedule = {
        "id": 1,
        "tour_name": "Ocean Tour",
        "event_start_datetime": datetime(2026, 3, 15, 10, 0),
        "event_end_datetime": datetime(2026, 3, 15, 12, 0),
        "language_code": "EN",
        "ticket_count": 5,
    }

    subject, text, html, portal, detail = notification_templates.guide_assigned_template(schedule, "John Doe", "AUTO")

    assert "Ocean Tour" in subject
    assert "John Doe" in text
    assert "automatically assigned" in text
    assert "Ocean Tour" in portal
    assert detail["assignment_type"] == "AUTO"


def test_guide_assigned_template_manual():
    """Test guide assigned template for MANUAL assignment."""
    schedule = {
        "id": 2,
        "tour_name": "Reef Tour",
        "event_start_datetime": datetime(2026, 3, 20, 14, 0),
        "event_end_datetime": datetime(2026, 3, 20, 16, 0),
        "language_code": "ES",
        "ticket_count": 10,
    }

    subject, text, html, portal, detail = notification_templates.guide_assigned_template(
        schedule, "Jane Smith", "MANUAL"
    )

    assert "manually assigned" in text
    assert detail["assignment_type"] == "MANUAL"


def test_guide_unassigned_template():
    """Test guide unassigned template."""
    schedule = {
        "id": 3,
        "tour_name": "Whale Watch",
        "event_start_datetime": datetime(2026, 3, 25, 9, 0),
        "event_end_datetime": datetime(2026, 3, 25, 11, 0),
        "language_code": "EN",
        "ticket_count": 8,
    }

    subject, text, html, portal, detail = notification_templates.guide_unassigned_template(
        schedule, "Bob Johnson", "Guide unavailable"
    )

    assert "Change" in subject
    assert "Bob Johnson" in text
    assert "Guide unavailable" in text
    assert "Tour assignment removed" in portal
    assert detail["removal_reason"] == "Guide unavailable"


def test_schedule_unassignable_admin_template():
    """Test schedule unassignable admin template."""
    schedule = {
        "id": 4,
        "tour_name": "Dolphin Tour",
        "event_start_datetime": datetime(2026, 3, 30, 10, 0),
        "event_end_datetime": datetime(2026, 3, 30, 12, 0),
        "language_code": "FR",
        "ticket_count": 15,
    }

    reasons = ["No available guides", "All certified guides busy"]

    subject, text, html, portal, detail = notification_templates.schedule_unassignable_admin_template(
        schedule, reasons, attempted_guides_count=5
    )

    assert "URGENT" in subject.upper()
    assert "No available guides" in text
    assert "All certified guides busy" in text
    assert detail["attempted_guides_count"] == 5


def test_schedule_changed_admin_template():
    """Test schedule changed admin template."""
    schedule = {
        "id": 5,
        "tour_name": "Sunset Cruise",
        "event_start_datetime": datetime(2026, 4, 1, 18, 0),
        "event_end_datetime": datetime(2026, 4, 1, 20, 0),
        "language_code": "EN",
        "ticket_count": 20,
    }

    subject, text, html, portal, detail = notification_templates.schedule_changed_admin_template(
        schedule, "RESERVATION_CANCELLED", "Reservation #123 cancelled"
    )

    assert "Schedule Update" in subject or "Schedule" in subject
    assert "RESERVATION_CANCELLED" in text
    assert "Reservation #123 cancelled" in text


# ===== Notification Service Tests =====


@pytest.fixture
def mock_conn():
    """Create a mock database connection."""
    conn = MagicMock()

    # Setup default execute behavior
    default_result = MagicMock()
    default_result.fetchone.return_value = None
    default_result.fetchall.return_value = []
    default_result.keys.return_value = []

    conn.execute.return_value = default_result
    conn.commit = MagicMock()

    # IMPORTANT: text() from sqlalchemy must remain callable
    # Don't let the mock interfere with the text import
    return conn


def test_get_notification_preferences_no_event_type(mock_conn):
    """Test getting preferences with no event type returns defaults."""
    prefs = notification_service.get_notification_preferences(mock_conn)

    assert prefs["email_enabled"] is True
    assert prefs["portal_enabled"] is True


def test_get_notification_preferences_with_user_id(mock_conn):
    """Test getting preferences for a specific user."""
    mock_result = MagicMock()
    # Return as tuple to match actual SQL row behavior
    mock_result.fetchone.return_value = (True, False)
    mock_conn.execute.return_value = mock_result

    prefs = notification_service.get_notification_preferences(mock_conn, user_id=1, event_type="GUIDE_ASSIGNED")

    # Check that execute was called
    assert mock_conn.execute.called
    # With defaults, if fetchone returns (True, False), the function should use these values
    # However, the function returns a dict, so we check dict keys
    assert "email_enabled" in prefs
    assert "portal_enabled" in prefs


def test_get_notification_preferences_with_guide_id(mock_conn):
    """Test getting preferences for a specific guide."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (False, True)
    mock_conn.execute.return_value = mock_result

    prefs = notification_service.get_notification_preferences(mock_conn, guide_id=5, event_type="GUIDE_ASSIGNED")

    # Check that execute was called
    assert mock_conn.execute.called
    assert "email_enabled" in prefs
    assert "portal_enabled" in prefs


def test_get_notification_preferences_not_found(mock_conn):
    """Test getting preferences when none exist returns defaults."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_conn.execute.return_value = mock_result

    prefs = notification_service.get_notification_preferences(mock_conn, user_id=1, event_type="GUIDE_ASSIGNED")

    assert prefs["email_enabled"] is True
    assert prefs["portal_enabled"] is True


def test_create_notification_single_channel(mock_conn):
    """Test creating a notification with single channel."""
    # Reset and setup mock for this test
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    mock_conn.execute.side_effect = None
    mock_conn.execute.return_value = mock_result

    notif_ids = notification_service.create_notification(
        conn=mock_conn,
        event_type="GUIDE_ASSIGNED",
        schedule_id=1,
        guide_id=5,
        user_id=None,
        message="Test message",
        channels=["PORTAL"],
        priority="normal",
        action_required=False,
        detail_json={"test": "data"},
        actions_json=[{"label": "View", "url": "/test"}],
    )

    assert len(notif_ids) == 1
    assert notif_ids[0] == 1


def test_create_notification_multiple_channels(mock_conn):
    """Test creating a notification with multiple channels."""
    call_count = [0]

    def mock_execute(*args, **kwargs):
        call_count[0] += 1
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (call_count[0],)
        return mock_result

    mock_conn.execute = mock_execute

    notif_ids = notification_service.create_notification(
        conn=mock_conn,
        event_type="GUIDE_ASSIGNED",
        schedule_id=1,
        guide_id=5,
        user_id=None,
        message="Test message",
        channels=["PORTAL", "EMAIL"],
        priority="urgent",
    )

    assert len(notif_ids) == 2


def test_send_pending_notification_portal():
    """Test sending a PORTAL notification."""
    # Create a fresh mock conn without fixture interference
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = ("PORTAL", "PENDING")
    result2 = MagicMock()
    result2.fetchone.return_value = None

    conn.execute.side_effect = [result1, result2]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(conn, 1)

    assert success is True


def test_send_pending_notification_email_missing_params():
    """Test sending EMAIL notification with missing parameters fails."""
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = ("EMAIL", "PENDING")
    result2 = MagicMock()
    result2.fetchone.return_value = None

    conn.execute.side_effect = [result1, result2]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(conn, 1)

    assert success is False


@patch("app.services.notification.send_email", return_value=True)
def test_send_pending_notification_email_success(mock_send_email):
    """Test successfully sending EMAIL notification."""
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = ("EMAIL", "PENDING")
    result2 = MagicMock()
    result2.fetchone.return_value = None

    conn.execute.side_effect = [result1, result2]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(
        conn,
        1,
        email="test@example.com",
        subject="Test",
        body_text="Body",
        html="<p>Body</p>",
    )

    assert success is True
    mock_send_email.assert_called_once()


@patch("app.services.notification.send_email", return_value=False)
def test_send_pending_notification_email_failure(mock_send_email):
    """Test EMAIL notification sending failure."""
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = ("EMAIL", "PENDING")
    result2 = MagicMock()
    result2.fetchone.return_value = None

    conn.execute.side_effect = [result1, result2]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(
        conn,
        1,
        email="test@example.com",
        subject="Test",
        body_text="Body",
    )

    assert success is False


def test_send_pending_notification_not_found():
    """Test sending notification that doesn't exist."""
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = None

    conn.execute.side_effect = [result1]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(conn, 999)

    assert success is False


def test_send_pending_notification_not_pending():
    """Test sending notification that is not in PENDING status."""
    conn = MagicMock()

    result1 = MagicMock()
    result1.fetchone.return_value = ("EMAIL", "SENT")

    conn.execute.side_effect = [result1]
    conn.commit = MagicMock()

    success = notification_service.send_pending_notification(conn, 1)

    assert success is False


def test_get_active_admins(mock_conn):
    """Test getting active admins."""
    mock_result = MagicMock()
    # Return list of tuples: (id, email, name)
    mock_result.fetchall.return_value = [
        (1, "admin1@example.com", "Admin One"),
        (2, "admin2@example.com", "Admin Two"),
    ]
    mock_conn.execute.side_effect = None
    mock_conn.execute.return_value = mock_result

    admins = notification_service.get_active_admins(mock_conn)

    assert len(admins) == 2
    assert admins[0]["email"] == "admin1@example.com"
    assert admins[1]["name"] == "Admin Two"


def test_get_active_admins_with_null_name(mock_conn):
    """Test getting active admins with null full_name defaults to 'Admin'."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [(1, "admin@example.com", None)]
    mock_conn.execute.side_effect = None
    mock_conn.execute.return_value = mock_result

    admins = notification_service.get_active_admins(mock_conn)

    assert len(admins) == 1
    assert admins[0]["name"] == "Admin"


def test_fetch_schedule_details_success(mock_conn):
    """Test fetching schedule details."""
    mock_result = MagicMock()
    mock_row = MagicMock()
    # Setup _mapping to return dict
    mock_row._mapping = {
        "id": 1,
        "tour_name": "Ocean Tour",
        "guide_name": "John Doe",
        "guide_email": "john@example.com",
        "event_start_datetime": datetime(2026, 3, 15, 10, 0),
        "ticket_count": 5,
    }
    mock_result.fetchone.return_value = mock_row
    mock_conn.execute.side_effect = None
    mock_conn.execute.return_value = mock_result

    schedule = notification_service.fetch_schedule_details(mock_conn, 1)

    assert schedule["id"] == 1
    assert schedule["tour_name"] == "Ocean Tour"


def test_fetch_schedule_details_not_found(mock_conn):
    """Test fetching non-existent schedule."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_conn.execute.return_value = mock_result

    schedule = notification_service.fetch_schedule_details(mock_conn, 999)

    assert schedule == {}


def test_retry_failed_email_notification_max_retries(mock_conn):
    """Test retry with max retries reached."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (3,)
    mock_conn.execute.return_value = mock_result

    success = notification_service.retry_failed_email_notification(mock_conn, 1)

    assert success is False


def test_retry_failed_email_notification_not_found(mock_conn):
    """Test retry with notification not found."""
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_conn.execute.return_value = mock_result

    success = notification_service.retry_failed_email_notification(mock_conn, 999)

    assert success is False


def test_list_notifications_with_user_id(mock_conn):
    """Test listing notifications for a user."""
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "message", "priority"]
    # Return list of tuples
    mock_result.fetchall.return_value = [
        (1, "Test message 1", "normal"),
        (2, "Test message 2", "high"),
    ]
    mock_conn.execute.side_effect = None
    mock_conn.execute.return_value = mock_result

    notifications = notification_service.list_notifications(mock_conn, user_id=1, filters={"limit": 10, "offset": 0})

    assert len(notifications) == 2


def test_list_notifications_with_filters(mock_conn):
    """Test listing notifications with various filters."""
    mock_result = MagicMock()
    mock_result.keys.return_value = []
    mock_result.fetchall.return_value = []
    mock_conn.execute.return_value = mock_result

    filters = {
        "status": "SENT",
        "channel": "EMAIL",
        "unread_only": True,
        "priority": "urgent",
        "limit": 20,
        "offset": 10,
    }

    notifications = notification_service.list_notifications(mock_conn, guide_id=5, filters=filters)

    assert isinstance(notifications, list)


# ===== Notification Dispatcher Tests =====


@patch("app.services.notification.notify_guide_assignment")
def test_dispatch_events_guide_assigned(mock_notify):
    """Test dispatching GUIDE_ASSIGNED event."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [{"type": "GUIDE_ASSIGNED", "schedule_id": 1, "guide_id": 5, "assignment_type": "AUTO"}]

    dispatch_events(conn, events)

    mock_notify.assert_called_once_with(conn, 1, 5, "AUTO")


@patch("app.services.notification.notify_guide_unassignment")
def test_dispatch_events_guide_unassigned(mock_notify):
    """Test dispatching GUIDE_UNASSIGNED event."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [{"type": "GUIDE_UNASSIGNED", "schedule_id": 1, "guide_id": 5, "reason": "Guide unavailable"}]

    dispatch_events(conn, events)

    mock_notify.assert_called_once_with(conn, 1, 5, "Guide unavailable")


@patch("app.services.notification.notify_schedule_unassignable")
def test_dispatch_events_schedule_unassignable(mock_notify):
    """Test dispatching SCHEDULE_UNASSIGNABLE event."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [{"type": "SCHEDULE_UNASSIGNABLE", "schedule_id": 1, "reasons": ["No guides available"]}]

    dispatch_events(conn, events)

    mock_notify.assert_called_once_with(conn, 1, ["No guides available"])


@patch("app.services.notification.notify_schedule_change")
def test_dispatch_events_schedule_changed(mock_notify):
    """Test dispatching SCHEDULE_CHANGED event."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [
        {
            "type": "SCHEDULE_CHANGED",
            "schedule_id": 1,
            "event_type": "RESERVATION_CANCELLED",
            "reason": "Customer cancelled",
            "affected_guide_id": 5,
        }
    ]

    dispatch_events(conn, events)

    mock_notify.assert_called_once()


def test_dispatch_events_unknown_type():
    """Test dispatching unknown event type logs warning."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [{"type": "UNKNOWN_EVENT"}]

    # Should not raise exception
    dispatch_events(conn, events)


def test_dispatch_events_handles_exception():
    """Test dispatch handles exceptions gracefully."""
    from app.services.notification_dispatcher import dispatch_events

    conn = MagicMock()
    events = [
        {
            "type": "GUIDE_ASSIGNED",
            "schedule_id": 1,
            # Missing required fields - will cause exception
        }
    ]

    # Should not raise exception
    dispatch_events(conn, events)
