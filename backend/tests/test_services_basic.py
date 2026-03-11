from unittest.mock import MagicMock

from app.services.guide import list_guides
from app.services.issue import create_issue
from app.services.notification import list_notifications
from app.services.stats import get_stats
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
