"""Unit tests for guide_language_service."""

from unittest.mock import MagicMock

import pytest

from app.services.exceptions import NotFoundError, ValidationError
from app.services.guide_language_service import get_guide_languages, update_guide_languages


class TestGetGuideLanguages:
    def test_guide_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        with pytest.raises(NotFoundError, match="Guide not found"):
            get_guide_languages(mock_conn, 99999)

    def test_guide_has_no_languages_returns_empty(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        langs_result = MagicMock()
        langs_result.fetchall.return_value = []
        mock_conn.execute.side_effect = [guide_result, langs_result]

        result = get_guide_languages(mock_conn, 1)

        assert result["languages"] == []

    def test_guide_has_languages_returns_list(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        langs_result = MagicMock()
        langs_result.fetchall.return_value = [(1, "English", "en"), (2, "French", "fr")]
        mock_conn.execute.side_effect = [guide_result, langs_result]

        result = get_guide_languages(mock_conn, 1)

        assert len(result["languages"]) == 2
        assert result["languages"][0] == {"id": 1, "name": "English", "code": "en"}
        assert result["languages"][1] == {"id": 2, "name": "French", "code": "fr"}


class TestUpdateGuideLanguages:
    def test_language_ids_must_be_list_raises(self, mock_conn):
        with pytest.raises(ValidationError, match="must be a list"):
            update_guide_languages(mock_conn, 1, "not a list")

    def test_guide_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        with pytest.raises(NotFoundError, match="Guide not found"):
            update_guide_languages(mock_conn, 99999, [1, 2])

    def test_invalid_language_id_raises(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        lang_check = MagicMock()
        lang_check.fetchone.return_value = None  # language 99999 not found
        mock_conn.execute.side_effect = [guide_result, lang_check]

        with pytest.raises(ValidationError, match="not found"):
            update_guide_languages(mock_conn, 1, [1, 99999])

    def test_success_clears_and_inserts(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        lang1 = MagicMock()
        lang1.fetchone.return_value = (1,)
        lang2 = MagicMock()
        lang2.fetchone.return_value = (2,)
        mock_conn.execute.side_effect = [guide_result, lang1, lang2, None, None, None]

        update_guide_languages(mock_conn, 1, [1, 2])

        mock_conn.commit.assert_called_once()

    def test_empty_list_clears_languages(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        mock_conn.execute.side_effect = [guide_result, None]  # delete, no inserts

        update_guide_languages(mock_conn, 1, [])

        mock_conn.commit.assert_called_once()
