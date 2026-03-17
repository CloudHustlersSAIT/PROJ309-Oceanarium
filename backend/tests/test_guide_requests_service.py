from unittest.mock import MagicMock, patch

from app.services.guide_requests import (
    accept_swap_request,
    create_swap_request,
    reject_swap_request,
)


def _swap_request_result(schedule_id=10, guide_id=3, original_guide_id=1):
    mappings_iter = MagicMock()
    mappings_iter.first.return_value = {
        "schedule_id": schedule_id,
        "guide_id": guide_id,
        "original_guide_id": original_guide_id,
    }
    result = MagicMock()
    result.mappings.return_value = mappings_iter
    return result


def _swap_not_found_result():
    mappings_iter = MagicMock()
    mappings_iter.first.return_value = None
    result = MagicMock()
    result.mappings.return_value = mappings_iter
    return result


def _schedule_lookup_result(schedule_id=10, guide_id=1):
    mappings_iter = MagicMock()
    mappings_iter.first.return_value = {
        "id": schedule_id,
        "guide_id": guide_id,
    }
    result = MagicMock()
    result.mappings.return_value = mappings_iter
    return result


def _insert_returning_result(row_id=1):
    result = MagicMock()
    result.fetchone.return_value = (row_id,)
    return result


class TestGuideRequestsService:
    @patch("app.services.guide_requests.notification_service")
    def test_accept_swap_success(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7, original_guide_id=5),
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT acceptance log
        ]

        result = accept_swap_request(mock_conn, swap_request_id=123, caller_guide_id=7)

        assert result["status"] == "accepted"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        assert result["original_guide_id"] == 5
        mock_conn.commit.assert_called_once()

        mock_notif.notify_guide_unassignment.assert_called_once_with(
            mock_conn,
            42,
            5,
            "Guide swap accepted",
            commit=False,
        )
        mock_notif.notify_guide_assignment.assert_called_once_with(
            mock_conn,
            42,
            7,
            "SWAP",
            commit=False,
        )
        mock_notif.notify_schedule_change.assert_called_once_with(
            mock_conn,
            42,
            change_type="GUIDE_SWAPPED",
            change_details="Guide swap completed. Guide 7 replaced Guide 5.",
            affected_guide_id=7,
            commit=False,
        )

    @patch("app.services.guide_requests.notification_service")
    def test_reject_swap_success(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7, original_guide_id=5),
            MagicMock(),  # INSERT rejection log
        ]

        result = reject_swap_request(mock_conn, swap_request_id=123, caller_guide_id=7)

        assert result["status"] == "rejected"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        mock_conn.commit.assert_called_once()

        mock_notif.notify_swap_request_rejected.assert_called_once_with(
            mock_conn,
            42,
            7,
            5,
            commit=False,
        )

    def test_accept_swap_not_found(self, mock_conn):
        mock_conn.execute.return_value = _swap_not_found_result()

        result = accept_swap_request(mock_conn, swap_request_id=999_999, caller_guide_id=1)

        assert result == {"status": "not_found"}
        mock_conn.commit.assert_not_called()

    @patch("app.services.guide_requests.notification_service")
    def test_accept_swap_notifications_failure_does_not_break_swap(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7, original_guide_id=5),
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT acceptance log
        ]
        mock_notif.notify_guide_unassignment.side_effect = RuntimeError("email down")
        mock_notif.notify_guide_assignment.side_effect = RuntimeError("email down")
        mock_notif.notify_schedule_change.side_effect = RuntimeError("email down")

        result = accept_swap_request(mock_conn, swap_request_id=123, caller_guide_id=7)

        assert result["status"] == "accepted"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        assert result["original_guide_id"] == 5
        mock_conn.commit.assert_called_once()

    @patch("app.services.guide_requests.notification_service")
    def test_create_swap_request_sends_notification(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_lookup_result(schedule_id=42, guide_id=5),
            _insert_returning_result(row_id=99),
        ]

        result = create_swap_request(mock_conn, schedule_id=42, guide_id=7, requesting_guide_id=5)

        assert result["swap_request_id"] == 99
        mock_conn.commit.assert_called_once()

        mock_notif.notify_swap_request_received.assert_called_once_with(
            mock_conn,
            42,
            7,
            5,
            commit=False,
        )

    @patch("app.services.guide_requests.notification_service")
    def test_create_swap_request_notification_failure_does_not_break(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_lookup_result(schedule_id=42, guide_id=5),
            _insert_returning_result(row_id=99),
        ]
        mock_notif.notify_swap_request_received.side_effect = RuntimeError("email down")

        result = create_swap_request(mock_conn, schedule_id=42, guide_id=7, requesting_guide_id=5)

        assert result["swap_request_id"] == 99
        mock_conn.commit.assert_called_once()

    @patch("app.services.guide_requests.notification_service")
    def test_reject_swap_sends_notification(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7, original_guide_id=5),
            MagicMock(),  # INSERT rejection log
        ]

        result = reject_swap_request(mock_conn, swap_request_id=123, caller_guide_id=7)

        assert result["status"] == "rejected"
        mock_conn.commit.assert_called_once()

        mock_notif.notify_swap_request_rejected.assert_called_once_with(
            mock_conn,
            42,
            7,
            5,
            commit=False,
        )

    @patch("app.services.guide_requests.notification_service")
    def test_reject_swap_notification_failure_does_not_break(self, mock_notif, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7, original_guide_id=5),
            MagicMock(),  # INSERT rejection log
        ]
        mock_notif.notify_swap_request_rejected.side_effect = RuntimeError("email down")

        result = reject_swap_request(mock_conn, swap_request_id=123, caller_guide_id=7)

        assert result["status"] == "rejected"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        mock_conn.commit.assert_called_once()
