from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.services.exceptions import NotFoundError, ValidationError
from app.services.schedule import create_schedule, list_schedules


class TestListSchedules:
    def test_returns_rows_as_dicts(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "tour_name", "status"]
        mock_result.fetchall.return_value = [(1, "Ocean Walk", "CONFIRMED")]
        mock_conn.execute.return_value = mock_result

        rows = list_schedules(mock_conn)

        assert len(rows) == 1
        assert rows[0]["id"] == 1
        assert rows[0]["tour_name"] == "Ocean Walk"

    def test_passes_filter_params(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        list_schedules(mock_conn, start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))

        call_args = mock_conn.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert params["start_date"] == date(2026, 1, 1)

    def test_raises_on_invalid_date_range(self, mock_conn):
        with pytest.raises(ValidationError):
            list_schedules(mock_conn, start_date=date(2026, 3, 10), end_date=date(2026, 3, 1))

    def test_normalizes_empty_status_to_none(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        list_schedules(mock_conn, status="  ")

        call_args = mock_conn.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]
        assert params["status"] is None


class TestCreateSchedule:
    def _make_payload(self, **overrides):
        defaults = {
            "guide_id": None,
            "tour_id": 1,
            "language_code": "en",
            "event_start_datetime": datetime(2026, 3, 10, 10, 0),
            "event_end_datetime": datetime(2026, 3, 10, 11, 0),
            "status": "CONFIRMED",
        }
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_raises_on_end_before_start(self, mock_conn):
        payload = self._make_payload(
            event_start_datetime=datetime(2026, 3, 10, 12, 0),
            event_end_datetime=datetime(2026, 3, 10, 10, 0),
        )
        with pytest.raises(ValidationError, match="event_end_datetime"):
            create_schedule(mock_conn, payload)

    def test_raises_on_empty_language_code(self, mock_conn):
        payload = self._make_payload(language_code="")
        with pytest.raises(ValidationError, match="language_code is required"):
            create_schedule(mock_conn, payload)

    def test_raises_on_long_language_code(self, mock_conn):
        payload = self._make_payload(language_code="eng")
        with pytest.raises(ValidationError, match="at most 2 characters"):
            create_schedule(mock_conn, payload)

    def test_raises_on_empty_status(self, mock_conn):
        payload = self._make_payload(status="  ")
        with pytest.raises(ValidationError, match="status cannot be empty"):
            create_schedule(mock_conn, payload)

    def test_raises_when_tour_not_found(self, mock_conn):
        payload = self._make_payload()
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="Tour not found"):
            create_schedule(mock_conn, payload)

    def test_raises_when_language_not_found(self, mock_conn):
        payload = self._make_payload()
        tour_result = MagicMock()
        tour_result.fetchone.return_value = MagicMock(id=1)
        lang_result = MagicMock()
        lang_result.fetchone.return_value = None
        mock_conn.execute.side_effect = [tour_result, lang_result]
        with pytest.raises(ValidationError, match="language_code not found"):
            create_schedule(mock_conn, payload)

    def test_raises_when_guide_not_found(self, mock_conn):
        payload = self._make_payload(guide_id=99)
        tour_result = MagicMock()
        tour_result.fetchone.return_value = MagicMock(id=1)
        lang_result = MagicMock()
        lang_result.fetchone.return_value = MagicMock(code="en")
        guide_result = MagicMock()
        guide_result.fetchone.return_value = None
        mock_conn.execute.side_effect = [tour_result, lang_result, guide_result]
        with pytest.raises(NotFoundError, match="Guide not found"):
            create_schedule(mock_conn, payload)

    def test_successful_create_returns_dict(self, mock_conn):
        payload = self._make_payload()
        tour_result = MagicMock()
        tour_result.fetchone.return_value = MagicMock(id=1)
        lang_result = MagicMock()
        lang_result.fetchone.return_value = MagicMock(code="en")
        insert_result = MagicMock()
        insert_result.keys.return_value = ["id", "tour_id", "status"]
        insert_result.fetchone.return_value = (1, 1, "CONFIRMED")
        mock_conn.execute.side_effect = [tour_result, lang_result, insert_result]

        result = create_schedule(mock_conn, payload)

        assert result["id"] == 1
        assert result["status"] == "CONFIRMED"
        mock_conn.commit.assert_called_once()
