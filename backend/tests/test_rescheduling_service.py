from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import NotFoundError, UnassignableError
from app.services.rescheduling import (
    cleanup_empty_schedule,
    find_matching_schedule,
    find_or_create_schedule,
    handle_guide_cancellation,
    handle_guide_cancellation_and_notify,
    handle_reservation_cancellation,
    handle_reservation_change,
)


def _scalar_one(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _fetchone(row):
    result = MagicMock()
    result.fetchone.return_value = row
    return result


def _schedule_mapping_row(
    schedule_id=1,
    guide_id=2,
    tour_id=10,
    language_code="en",
    event_start="2026-03-10T10:00:00Z",
    event_end="2026-03-10T11:00:00Z",
    status="ASSIGNED",
):
    row = MagicMock()
    row._mapping = {
        "id": schedule_id,
        "guide_id": guide_id,
        "tour_id": tour_id,
        "language_code": language_code,
        "event_start_datetime": event_start,
        "event_end_datetime": event_end,
        "status": status,
    }
    row.__getitem__ = lambda self, i: [schedule_id, guide_id][i]
    return row


class TestFindMatchingSchedule:
    def test_returns_id_when_match_found(self, mock_conn):
        mock_conn.execute.return_value = _fetchone((42,))
        result = find_matching_schedule(mock_conn, 10, "en", "2026-03-10T10:00:00Z")
        assert result == 42

    def test_returns_none_when_no_match(self, mock_conn):
        mock_conn.execute.return_value = _fetchone(None)
        result = find_matching_schedule(mock_conn, 10, "en", "2026-03-10T10:00:00Z")
        assert result is None


class TestFindOrCreateSchedule:
    @patch("app.services.rescheduling.find_matching_schedule")
    def test_returns_existing_schedule(self, mock_find, mock_conn):
        mock_find.return_value = 42
        result = find_or_create_schedule(mock_conn, 10, "en", "2026-03-10T10:00:00Z", "2026-03-10T11:00:00Z")
        assert result == 42  # Returns int, not tuple
        mock_conn.execute.assert_not_called()

    @patch("app.services.rescheduling.auto_assign_guide")
    @patch("app.services.rescheduling.find_matching_schedule")
    def test_creates_schedule_and_assigns_guide(self, mock_find, mock_assign, mock_conn):
        mock_find.return_value = None
        mock_conn.execute.return_value = _fetchone((99,))
        mock_assign.return_value = {"guide_id": 5, "guide_name": "Maria Silva"}

        result = find_or_create_schedule(mock_conn, 10, "en", "2026-03-10T10:00:00Z", "2026-03-10T11:00:00Z")

        assert result == 99  # Returns int
        mock_assign.assert_called_once_with(mock_conn, 99, commit=False)

    @patch("app.services.rescheduling.auto_assign_guide")
    @patch("app.services.rescheduling.find_matching_schedule")
    def test_creates_schedule_unassignable(self, mock_find, mock_assign, mock_conn):
        mock_find.return_value = None
        mock_conn.execute.return_value = _fetchone((99,))
        mock_assign.side_effect = UnassignableError("No guide", reasons=["NO_LANGUAGE_MATCH"])

        result = find_or_create_schedule(mock_conn, 10, "zh", "2026-03-10T10:00:00Z", "2026-03-10T11:00:00Z")

        assert result == 99  # Returns int even when unassignable


class TestCleanupEmptySchedule:
    def test_does_nothing_when_active_reservations_remain(self, mock_conn):
        mock_conn.execute.return_value = _scalar_one(3)
        cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 1

    def test_cancels_schedule_with_guide(self, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone((1, 5)),  # schedule row: id=1, guide_id=5
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT tour_assignment_logs
        ]
        result = cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 4
        assert isinstance(result, dict)
        assert result.get("old_guide_id") == 5

    def test_cancels_schedule_without_guide(self, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone((1, None)),  # schedule with no guide
            MagicMock(),  # UPDATE schedule
        ]
        result = cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 3
        assert result == {}

    def test_does_nothing_when_schedule_not_found(self, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone(None),
        ]
        result = cleanup_empty_schedule(mock_conn, 999)
        assert mock_conn.execute.call_count == 2
        assert result == {}


class TestHandleReservationChange:
    @patch("app.services.rescheduling.cleanup_empty_schedule")
    @patch("app.services.rescheduling.find_or_create_schedule")
    def test_moves_reservation_to_new_schedule(self, mock_find_create, mock_cleanup, mock_conn):
        mock_find_create.return_value = 50  # Returns int now
        # Mock the SELECT guide_id query
        mock_guide_result = MagicMock()
        mock_guide_result.fetchone.return_value = (5,)  # guide_id = 5
        mock_conn.execute.return_value = mock_guide_result

        handle_reservation_change(
            mock_conn,
            reservation_id=10,
            old_schedule_id=20,
            new_tour_id=1,
            new_language_code="pt",
            new_event_start="2026-03-11T10:00:00Z",
            new_event_end="2026-03-11T11:00:00Z",
        )

        assert mock_conn.execute.call_count == 3  # 2 UPDATEs + 1 SELECT
        mock_find_create.assert_called_once()
        mock_cleanup.assert_called_once_with(mock_conn, 20)

    @patch("app.services.rescheduling.cleanup_empty_schedule")
    @patch("app.services.rescheduling.find_or_create_schedule")
    def test_no_cleanup_when_old_schedule_is_none(self, mock_find_create, mock_cleanup, mock_conn):
        mock_find_create.return_value = 50  # Returns int now

        handle_reservation_change(
            conn=mock_conn,
            reservation_id=10,
            old_schedule_id=None,
            new_tour_id=1,
            new_language_code="en",
            new_event_start="2026-03-11T10:00:00Z",
            new_event_end="2026-03-11T11:00:00Z",
        )

        mock_cleanup.assert_not_called()


class TestHandleReservationCancellation:
    @patch("app.services.rescheduling.cleanup_empty_schedule")
    def test_notifies_and_cleans_up(self, mock_cleanup, mock_conn):
        handle_reservation_cancellation(mock_conn, reservation_id=10, old_schedule_id=20)

        mock_cleanup.assert_called_once_with(mock_conn, 20)


class TestHandleGuideCancellation:
    def test_schedule_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value = _fetchone(None)
        with pytest.raises(NotFoundError, match="Schedule not found"):
            handle_guide_cancellation(mock_conn, 999)

    def test_no_guide_assigned(self, mock_conn):
        row = _schedule_mapping_row(guide_id=None, status="UNASSIGNED")
        mock_conn.execute.return_value = _fetchone(row)

        result = handle_guide_cancellation(mock_conn, 1)

        assert result["message"] == "No guide was assigned"

    @patch("app.services.rescheduling.auto_assign_guide")
    def test_replacement_guide_found(self, mock_assign, mock_conn):
        row = _schedule_mapping_row(schedule_id=1, guide_id=5, status="ASSIGNED")
        mock_conn.execute.side_effect = [
            _fetchone(row),
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT tour_assignment_logs
        ]
        mock_assign.return_value = {"guide_id": 7, "guide_name": "Carlos Santos"}

        result = handle_guide_cancellation(mock_conn, 1)

        assert result["old_guide_id"] == 5
        assert result["new_guide_id"] == 7
        assert result["status"] == "ASSIGNED"
        mock_conn.commit.assert_called_once()

    @patch("app.services.rescheduling.auto_assign_guide")
    def test_no_replacement_guide(self, mock_assign, mock_conn):
        row = _schedule_mapping_row(schedule_id=1, guide_id=5, status="ASSIGNED")
        mock_conn.execute.side_effect = [
            _fetchone(row),
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT tour_assignment_logs
        ]
        mock_assign.side_effect = UnassignableError("No guide", reasons=["NO_AVAILABILITY_MATCH"])

        result = handle_guide_cancellation(mock_conn, 1)

        assert result["old_guide_id"] == 5
        assert result["new_guide_id"] is None
        assert result["status"] == "UNASSIGNABLE"
        assert "NO_AVAILABILITY_MATCH" in result["reasons"]
        mock_conn.commit.assert_called_once()


# ===== handle_guide_cancellation_and_notify Tests =====


class TestHandleGuideCancellationAndNotify:
    def test_replacement_found_sends_both_notifications(self):
        with (
            patch("app.services.rescheduling.handle_guide_cancellation") as mock_cancel,
            patch("app.services.rescheduling.notification_service") as mock_notif,
        ):
            mock_cancel.return_value = {
                "schedule_id": 1,
                "old_guide_id": 5,
                "new_guide_id": 8,
                "status": "ASSIGNED",
            }
            conn = MagicMock()

            result = handle_guide_cancellation_and_notify(conn, 1)

        assert result["new_guide_id"] == 8
        mock_notif.notify_guide_unassignment.assert_called_once_with(conn, 1, 5, "Guide requested cancellation")
        mock_notif.notify_guide_assignment.assert_called_once_with(conn, 1, 8, "AUTO")

    def test_unassignable_sends_unassignment_and_unassignable_notifications(self):
        with (
            patch("app.services.rescheduling.handle_guide_cancellation") as mock_cancel,
            patch("app.services.rescheduling.notification_service") as mock_notif,
        ):
            mock_cancel.return_value = {
                "schedule_id": 1,
                "old_guide_id": 5,
                "new_guide_id": None,
                "status": "UNASSIGNABLE",
                "reasons": ["NO_AVAILABILITY_MATCH"],
            }
            conn = MagicMock()

            result = handle_guide_cancellation_and_notify(conn, 1)

        assert result["status"] == "UNASSIGNABLE"
        mock_notif.notify_guide_unassignment.assert_called_once()
        mock_notif.notify_schedule_unassignable.assert_called_once_with(conn, 1, ["NO_AVAILABILITY_MATCH"])

    def test_no_old_guide_skips_unassignment_notification(self):
        with (
            patch("app.services.rescheduling.handle_guide_cancellation") as mock_cancel,
            patch("app.services.rescheduling.notification_service") as mock_notif,
        ):
            mock_cancel.return_value = {
                "schedule_id": 1,
                "status": "UNASSIGNED",
                "message": "No guide was assigned",
            }
            conn = MagicMock()

            result = handle_guide_cancellation_and_notify(conn, 1)

        assert result["message"] == "No guide was assigned"
        mock_notif.notify_guide_unassignment.assert_not_called()
        mock_notif.notify_guide_assignment.assert_not_called()

    def test_notification_failure_does_not_break_flow(self):
        with (
            patch("app.services.rescheduling.handle_guide_cancellation") as mock_cancel,
            patch("app.services.rescheduling.notification_service") as mock_notif,
        ):
            mock_cancel.return_value = {
                "schedule_id": 1,
                "old_guide_id": 5,
                "new_guide_id": 8,
                "status": "ASSIGNED",
            }
            mock_notif.notify_guide_unassignment.side_effect = RuntimeError("email down")
            conn = MagicMock()

            result = handle_guide_cancellation_and_notify(conn, 1)

        assert result["new_guide_id"] == 8
