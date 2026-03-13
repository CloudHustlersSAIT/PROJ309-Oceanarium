from unittest.mock import MagicMock

from app.services.guide_dashboard import get_dashboard


class TestGetDashboard:
    def test_returns_all_dashboard_fields(self, mock_conn):
        next_tour = {"id": 1, "tour_name": "Shark Dive", "event_start_datetime": "2026-04-01T10:00:00"}
        next_tour_result = MagicMock()
        next_tour_result.mappings.return_value.first.return_value = next_tour

        week_result = MagicMock()
        week_result.scalar.return_value = 3

        pending_result = MagicMock()
        pending_result.scalar.return_value = 1

        rating_result = MagicMock()
        rating_result.scalar.return_value = 4.5

        today_result = MagicMock()
        today_result.mappings.return_value.all.return_value = [
            {"id": 10, "name": "Ocean Walk", "status": "scheduled"},
        ]

        mock_conn.execute.side_effect = [
            next_tour_result,
            week_result,
            pending_result,
            rating_result,
            today_result,
        ]

        result = get_dashboard(mock_conn, guide_id=5)

        assert result["next_tour"] == next_tour
        assert result["tours_this_week"] == 3
        assert result["pending_requests"] == 1
        assert result["rating"] == 4.5
        assert len(result["today_schedule"]) == 1

    def test_returns_none_next_tour_when_empty(self, mock_conn):
        next_tour_result = MagicMock()
        next_tour_result.mappings.return_value.first.return_value = None

        week_result = MagicMock()
        week_result.scalar.return_value = 0

        pending_result = MagicMock()
        pending_result.scalar.return_value = 0

        rating_result = MagicMock()
        rating_result.scalar.return_value = None

        today_result = MagicMock()
        today_result.mappings.return_value.all.return_value = []

        mock_conn.execute.side_effect = [
            next_tour_result,
            week_result,
            pending_result,
            rating_result,
            today_result,
        ]

        result = get_dashboard(mock_conn, guide_id=99)

        assert result["next_tour"] is None
        assert result["tours_this_week"] == 0
        assert result["today_schedule"] == []
