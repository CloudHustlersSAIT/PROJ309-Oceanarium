from datetime import date
from unittest.mock import MagicMock

from app.services.guide import list_guides
from app.services.issue import create_issue
from app.services.notification import create_notification, list_notifications
from app.services.stats import get_admin_dashboard, get_stats
from app.services.tour import list_tours


class TestGuideService:
    def test_list_guides(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "first_name"]
        mock_result.fetchall.return_value = [(1, "Maria"), (2, "João")]
        mock_conn.execute.return_value = mock_result

        rows = list_guides(mock_conn)
        assert len(rows) == 2
        assert rows[0]["first_name"] == "Maria"


class TestTourService:
    def test_list_tours(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "Ocean Walk")]
        mock_conn.execute.return_value = mock_result

        rows = list_tours(mock_conn)
        assert len(rows) == 1
        assert rows[0]["name"] == "Ocean Walk"


class TestNotificationService:
    def test_list_notifications(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "message"]
        mock_result.fetchall.return_value = [(1, "Alert")]
        mock_conn.execute.return_value = mock_result

        rows = list_notifications(mock_conn)
        assert len(rows) == 1

    def test_create_notification(self, mock_conn):
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_conn.execute.return_value = mock_result

        result = create_notification(
            mock_conn,
            event_type="GUIDE_ASSIGNED",
            schedule_id=1,
            guide_id=5,
            user_id=None,
            message="Test",
            channels=["PORTAL"],
        )
        assert mock_conn.execute.called
        assert isinstance(result, list)


class TestIssueService:
    def test_create_issue(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "description"]
        mock_result.fetchone.return_value = (1, "Broken pump")
        mock_conn.execute.return_value = mock_result

        issue = MagicMock(description="Broken pump")
        result = create_issue(mock_conn, issue)
        assert result["id"] == 1
        mock_conn.commit.assert_called_once()


class TestStatsService:
    def test_get_stats(self, mock_conn):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_conn.execute.return_value = mock_result

        result = get_stats(mock_conn)
        assert result["toursToday"] == 5
        assert "customersToday" in result
        assert "cancellations" in result
        assert "avgRating" in result

    def test_get_admin_dashboard(self, mock_conn):
        kpi_result = MagicMock()
        kpi_result.mappings.return_value.one.return_value = {
            "total_tours_conducted": 9,
            "total_visitors_served": 42,
            "avg_guide_rating": 4.75,
        }

        tours_per_year_result = MagicMock()
        tours_per_year_result.mappings.return_value.all.return_value = [
            {"year": 2026, "value": 9},
        ]

        visitors_per_tour_result = MagicMock()
        visitors_per_tour_result.mappings.return_value.all.return_value = [
            {"label": "Shark Diving", "value": 42},
        ]

        tours_by_language_result = MagicMock()
        tours_by_language_result.mappings.return_value.all.return_value = [
            {"label": "English", "code": "en", "value": 6},
        ]

        bookings_vs_cancellations_result = MagicMock()
        bookings_vs_cancellations_result.mappings.return_value.all.return_value = [
            {"month": "Mar 2026", "bookings": 11, "cancellations": 2},
        ]

        top_guides_result = MagicMock()
        top_guides_result.mappings.return_value.all.return_value = [
            {"name": "Ana Costa", "tours": 4, "rating": 4.9},
        ]

        mock_conn.execute.side_effect = [
            kpi_result,
            tours_per_year_result,
            visitors_per_tour_result,
            tours_by_language_result,
            bookings_vs_cancellations_result,
            top_guides_result,
        ]

        result = get_admin_dashboard(mock_conn, selected_date=date(2026, 3, 12), period="all_time")

        assert result["filters"]["selectedDate"] == "2026-03-12"
        assert result["kpis"]["totalToursConducted"] == 9
        assert result["kpis"]["totalVisitorsServed"] == 42
        assert result["kpis"]["avgGuideRating"] == 4.75
        assert result["kpis"]["avgOccupancyRate"] is None
        assert result["toursPerYear"][0]["label"] == "2026"
        assert result["visitorsPerTour"][0]["label"] == "Shark Diving"
        assert result["toursByLanguage"][0]["code"] == "en"
        assert result["bookingsVsCancellations"][0]["month"] == "Mar 2026"
        assert result["topRatedGuides"][0]["name"] == "Ana Costa"
        assert result["meta"]["occupancyRateAvailable"] is False
