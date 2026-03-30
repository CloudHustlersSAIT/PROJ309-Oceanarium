from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import ValidationError
from app.services.guide import create_guide, soft_delete_guide, update_guide


def _guide_row(guide_id: int, first_name: str = "Maria", last_name: str = "Silva", email: str = "maria@test.com"):
    row = MagicMock()
    row._mapping = {
        "id": guide_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": None,
        "guide_rating": None,
        "is_active": True,
    }
    return row


class TestCreateGuide:
    def test_moderates_name_fields(self, mock_conn):
        insert_result = MagicMock()
        insert_result.fetchone.return_value = MagicMock(id=7)

        mock_conn.execute.side_effect = [
            insert_result,
            MagicMock(),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        with (
            patch("app.services.guide.assert_text_is_safe") as mock_safe,
            patch("app.services.guide._fetch_guide_profile", return_value={"id": 7}),
        ):
            create_guide(mock_conn, "Maria", "Silva", "maria@test.com")

        assert mock_safe.call_count == 2

    def test_create_guide_with_relations(self, mock_conn):
        insert_result = MagicMock()
        insert_result.fetchone.return_value = MagicMock(id=7)

        languages_result = MagicMock()
        languages_result.fetchall.return_value = [MagicMock(id=1, code="en")]

        tours_result = MagicMock()
        tours_result.fetchall.return_value = [MagicMock(id=10)]

        pattern_insert_result = MagicMock()
        pattern_insert_result.fetchone.return_value = MagicMock(id=20)

        empty_rows = MagicMock()
        empty_rows.fetchall.return_value = []

        mock_conn.execute.side_effect = [
            insert_result,
            MagicMock(),
            languages_result,
            MagicMock(),
            MagicMock(),
            tours_result,
            MagicMock(),
            MagicMock(),
            pattern_insert_result,
            MagicMock(),
            MagicMock(),
        ]

        with patch(
            "app.services.guide._fetch_guide_profile",
            return_value={
                "id": 7,
                "first_name": "Maria",
                "last_name": "Silva",
                "email": "maria@test.com",
                "language_codes": ["en"],
                "expertise_tour_ids": [10],
                "availability_patterns": [{"id": 20, "timezone": "Europe/Lisbon", "slots": []}],
            },
        ):
            result = create_guide(
                mock_conn,
                "Maria",
                "Silva",
                "maria@test.com",
                language_codes=["EN"],
                expertise_tour_ids=[10],
                availability_patterns=[
                    {
                        "timezone": "Europe/Lisbon",
                        "slots": [
                            {
                                "day_of_week": "monday",
                                "start_time": time(9, 0),
                                "end_time": time(17, 0),
                            }
                        ],
                    }
                ],
            )

        assert result["id"] == 7
        assert result["language_codes"] == ["en"]
        assert result["expertise_tour_ids"] == [10]
        assert len(result["availability_patterns"]) == 1
        mock_conn.commit.assert_called_once()

    def test_create_guide_rejects_invalid_day(self, mock_conn):
        insert_result = MagicMock()
        insert_result.fetchone.return_value = MagicMock(id=9)

        mock_conn.execute.side_effect = [insert_result, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        with pytest.raises(ValidationError, match="Invalid day_of_week"):
            create_guide(
                mock_conn,
                "Maria",
                "Silva",
                "maria@test.com",
                availability_patterns=[
                    {
                        "timezone": "UTC",
                        "slots": [
                            {
                                "day_of_week": "funday",
                                "start_time": time(9, 0),
                                "end_time": time(10, 0),
                            }
                        ],
                    }
                ],
            )


class TestUpdateGuide:
    def test_update_guide_partial_fields(self, mock_conn):
        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=MagicMock())),
            MagicMock(),
        ]

        with patch(
            "app.services.guide._fetch_guide_profile",
            return_value={"id": 3, "first_name": "Ana", "last_name": "Silva", "email": "ana@test.com"},
        ):
            result = update_guide(mock_conn, 3, {"first_name": "Ana"})

        assert result["first_name"] == "Ana"
        mock_conn.commit.assert_called_once()

    def test_update_guide_not_found(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        result = update_guide(mock_conn, 999, {"first_name": "Ana"})

        assert result is None

    def test_update_guide_moderates_name_fields(self, mock_conn):
        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=MagicMock())),
            MagicMock(),
        ]

        with (
            patch("app.services.guide.assert_text_is_safe") as mock_safe,
            patch("app.services.guide._fetch_guide_profile", return_value={"id": 3}),
        ):
            update_guide(mock_conn, 3, {"first_name": "Ana", "last_name": "Costa"})

        assert mock_safe.call_count == 2


class TestSoftDeleteGuide:
    def test_soft_delete_guide_success(self, mock_conn):
        mock_conn.execute.return_value = MagicMock(fetchone=MagicMock(return_value=MagicMock(id=3)))

        with patch(
            "app.services.guide._fetch_guide_profile",
            return_value={"id": 3, "is_active": False},
        ):
            result = soft_delete_guide(mock_conn, 3)

        assert result["id"] == 3
        assert result["is_active"] is False
        mock_conn.commit.assert_called_once()

    def test_soft_delete_guide_not_found(self, mock_conn):
        mock_conn.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))

        result = soft_delete_guide(mock_conn, 999)

        assert result is None
        mock_conn.commit.assert_not_called()
