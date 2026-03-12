from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import NotFoundError, UnassignableError
from app.services.rescheduling import (
    cleanup_empty_schedule,
    find_matching_schedule,
    find_or_create_schedule,
    handle_guide_cancellation,
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
        assert result == 42
        mock_conn.execute.assert_not_called()

    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.auto_assign_guide")
    @patch("app.services.rescheduling.find_matching_schedule")
    def test_creates_schedule_and_assigns_guide(self, mock_find, mock_assign, mock_notify, mock_conn):
        mock_find.return_value = None
        mock_conn.execute.return_value = _fetchone((99,))
        mock_assign.return_value = {"guide_id": 5, "guide_name": "Maria Silva"}

        result = find_or_create_schedule(mock_conn, 10, "en", "2026-03-10T10:00:00Z", "2026-03-10T11:00:00Z")

        assert result == 99
        mock_assign.assert_called_once_with(mock_conn, 99, commit=False)
        assert mock_notify.call_count == 1
        assert mock_notify.call_args[1]["event_type"] == "GUIDE_ASSIGNED"

    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.auto_assign_guide")
    @patch("app.services.rescheduling.find_matching_schedule")
    def test_creates_schedule_unassignable(self, mock_find, mock_assign, mock_notify, mock_conn):
        mock_find.return_value = None
        mock_conn.execute.return_value = _fetchone((99,))
        mock_assign.side_effect = UnassignableError("No guide", reasons=["NO_LANGUAGE_MATCH"])

        result = find_or_create_schedule(mock_conn, 10, "zh", "2026-03-10T10:00:00Z", "2026-03-10T11:00:00Z")

        assert result == 99
        assert mock_notify.call_count == 1
        assert mock_notify.call_args[1]["event_type"] == "SCHEDULE_UNASSIGNABLE"


class TestCleanupEmptySchedule:
    @patch("app.services.rescheduling.create_notification")
    def test_does_nothing_when_active_reservations_remain(self, mock_notify, mock_conn):
        mock_conn.execute.return_value = _scalar_one(3)
        cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 1
        mock_notify.assert_not_called()

    @patch("app.services.rescheduling.create_notification")
    def test_cancels_schedule_with_guide(self, mock_notify, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone((1, 5)),  # schedule row: id=1, guide_id=5
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT tour_assignment_logs
        ]
        cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 4
        mock_notify.assert_called_once()
        assert mock_notify.call_args[1]["event_type"] == "GUIDE_REASSIGNED"

    @patch("app.services.rescheduling.create_notification")
    def test_cancels_schedule_without_guide(self, mock_notify, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone((1, None)),  # schedule with no guide
            MagicMock(),  # UPDATE schedule
        ]
        cleanup_empty_schedule(mock_conn, 1)
        assert mock_conn.execute.call_count == 3
        mock_notify.assert_not_called()

    @patch("app.services.rescheduling.create_notification")
    def test_does_nothing_when_schedule_not_found(self, mock_notify, mock_conn):
        mock_conn.execute.side_effect = [
            _scalar_one(0),
            _fetchone(None),
        ]
        cleanup_empty_schedule(mock_conn, 999)
        assert mock_conn.execute.call_count == 2
        mock_notify.assert_not_called()


class TestHandleReservationChange:
    @patch("app.services.rescheduling.cleanup_empty_schedule")
    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.find_or_create_schedule")
    def test_moves_reservation_to_new_schedule(self, mock_find_create, mock_notify, mock_cleanup, mock_conn):
        mock_find_create.return_value = 50

        handle_reservation_change(
            mock_conn,
            reservation_id=10,
            old_schedule_id=20,
            new_tour_id=1,
            new_language_code="pt",
            new_event_start="2026-03-11T10:00:00Z",
            new_event_end="2026-03-11T11:00:00Z",
        )

        assert mock_conn.execute.call_count == 2
        mock_find_create.assert_called_once()
        mock_notify.assert_called_once()
        assert "moved" in mock_notify.call_args[1]["message"].lower()
        mock_cleanup.assert_called_once_with(mock_conn, 20)

    @patch("app.services.rescheduling.cleanup_empty_schedule")
    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.find_or_create_schedule")
    def test_no_cleanup_when_old_schedule_is_none(self, mock_find_create, mock_notify, mock_cleanup, mock_conn):
        mock_find_create.return_value = 50

        handle_reservation_change(
            mock_conn,
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
    @patch("app.services.rescheduling.create_notification")
    def test_notifies_and_cleans_up(self, mock_notify, mock_cleanup, mock_conn):
        handle_reservation_cancellation(mock_conn, reservation_id=10, old_schedule_id=20)

        mock_notify.assert_called_once()
        assert mock_notify.call_args[1]["event_type"] == "RESERVATION_CANCELLED"
        mock_cleanup.assert_called_once_with(mock_conn, 20)


class TestHandleGuideCancellation:
    def test_schedule_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value = _fetchone(None)
        with pytest.raises(NotFoundError, match="Schedule not found"):
            handle_guide_cancellation(mock_conn, 999)

    @patch("app.services.rescheduling.create_notification")
    def test_no_guide_assigned(self, mock_notify, mock_conn):
        row = _schedule_mapping_row(guide_id=None, status="UNASSIGNED")
        mock_conn.execute.return_value = _fetchone(row)

        result = handle_guide_cancellation(mock_conn, 1)

        assert result["message"] == "No guide was assigned"
        mock_notify.assert_not_called()

    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.auto_assign_guide")
    def test_replacement_guide_found(self, mock_assign, mock_notify, mock_conn):
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

    @patch("app.services.rescheduling.create_notification")
    @patch("app.services.rescheduling.auto_assign_guide")
    def test_no_replacement_guide(self, mock_assign, mock_notify, mock_conn):
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
