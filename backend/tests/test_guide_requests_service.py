from unittest.mock import MagicMock

from app.services.guide_requests import accept_swap_request, reject_swap_request


def _swap_request_result(schedule_id=10, guide_id=3):
    mappings_iter = MagicMock()
    mappings_iter.first.return_value = {
        "schedule_id": schedule_id,
        "guide_id": guide_id,
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


class TestGuideRequestsService:
    def test_accept_swap_success(self, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7),
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT acceptance log
        ]

        result = accept_swap_request(mock_conn, swap_request_id=123)

        assert result["status"] == "accepted"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        mock_conn.commit.assert_called_once()

    def test_reject_swap_success(self, mock_conn):
        mock_conn.execute.side_effect = [
            _swap_request_result(schedule_id=42, guide_id=7),
            MagicMock(),  # INSERT rejection log
        ]

        result = reject_swap_request(mock_conn, swap_request_id=123)

        assert result["status"] == "rejected"
        assert result["schedule_id"] == 42
        assert result["guide_id"] == 7
        mock_conn.commit.assert_called_once()

    def test_accept_swap_not_found(self, mock_conn):
        mock_conn.execute.return_value = _swap_not_found_result()

        result = accept_swap_request(mock_conn, swap_request_id=999_999)

        assert result == {"status": "not_found"}
        mock_conn.commit.assert_not_called()
