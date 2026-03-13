from unittest.mock import MagicMock

from app.services.language import list_languages


class TestListLanguages:
    def test_returns_languages(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "code", "name"]
        mock_result.fetchall.return_value = [(1, "en", "English"), (2, "pt", "Portuguese")]
        mock_conn.execute.return_value = mock_result

        rows = list_languages(mock_conn)

        assert len(rows) == 2
        assert rows[0]["code"] == "en"
        assert rows[1]["name"] == "Portuguese"

    def test_returns_empty_list(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "code", "name"]
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        rows = list_languages(mock_conn)

        assert rows == []
