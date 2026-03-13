"""Unit tests for guide_availability_service."""

from datetime import time
from unittest.mock import MagicMock

import pytest

from app.services.exceptions import NotFoundError, ValidationError
from app.services.guide_availability_service import (
    _normalize_day,
    _parse_time,
    get_guide_availability,
    update_guide_availability,
)


class TestNormalizeDay:
    def test_short_form(self):
        assert _normalize_day("mon") == "Monday"
        assert _normalize_day("tue") == "Tuesday"
        assert _normalize_day("sun") == "Sunday"

    def test_full_name(self):
        assert _normalize_day("Monday") == "Monday"
        assert _normalize_day("Friday") == "Friday"

    def test_case_insensitive_full(self):
        assert _normalize_day("monday") == "Monday"
        assert _normalize_day("FRIDAY") == "Friday"

    def test_blank_raises(self):
        # Empty string raises "day is required and must be a non-empty string"
        with pytest.raises(ValidationError, match="required|non-empty|blank"):
            _normalize_day("")
        # Whitespace-only raises "day cannot be blank"
        with pytest.raises(ValidationError, match="cannot be blank"):
            _normalize_day("   ")

    def test_invalid_day_raises(self):
        with pytest.raises(ValidationError, match="Invalid day"):
            _normalize_day("Notaday")
        with pytest.raises(ValidationError, match="required"):
            _normalize_day(None)


class TestParseTime:
    def test_valid_hhmm(self):
        t = _parse_time("09:00")
        assert t == time(9, 0, 0)
        t = _parse_time("23:59")
        assert t == time(23, 59, 0)

    def test_valid_hhmmss(self):
        t = _parse_time("09:00:30")
        assert t == time(9, 0, 30)

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="Invalid time format"):
            _parse_time("not-a-time")
        with pytest.raises(ValidationError, match="Invalid time format"):
            _parse_time("1:2")  # too short, no leading zero in minutes
        with pytest.raises(ValidationError, match="non-empty"):
            _parse_time("")

    def test_out_of_range_raises(self):
        with pytest.raises(ValidationError, match="out of range"):
            _parse_time("24:00")
        with pytest.raises(ValidationError, match="out of range"):
            _parse_time("12:60")


class TestGetGuideAvailability:
    def test_no_pattern_returns_default_and_empty_slots(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        result = get_guide_availability(mock_conn, 1)

        assert result["timezone"] == "UTC"
        assert result["slots"] == []

    def test_with_pattern_and_slots(self, mock_conn):
        pattern_result = MagicMock()
        pattern_result.fetchone.return_value = (10, "America/New_York")
        slots_result = MagicMock()
        slots_result.fetchall.return_value = [
            ("Monday", time(9, 0), time(17, 0)),
            ("Tuesday", time(10, 0), time(16, 0)),
        ]
        mock_conn.execute.side_effect = [pattern_result, slots_result]

        result = get_guide_availability(mock_conn, 1)

        assert result["timezone"] == "America/New_York"
        assert len(result["slots"]) == 2
        assert result["slots"][0]["day"] == "Monday"
        assert result["slots"][0]["start"] == "09:00"
        assert result["slots"][0]["end"] == "17:00"


class TestUpdateGuideAvailability:
    def test_guide_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        with pytest.raises(NotFoundError, match="Guide not found"):
            update_guide_availability(mock_conn, 99999, [{"day": "Monday", "start": "09:00", "end": "17:00"}])

    def test_invalid_slot_start_after_end_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = (1,)  # guide exists

        with pytest.raises(ValidationError, match="before end time"):
            update_guide_availability(mock_conn, 1, [{"day": "Monday", "start": "17:00", "end": "09:00"}])

    def test_invalid_day_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        with pytest.raises(ValidationError, match="Invalid day"):
            update_guide_availability(mock_conn, 1, [{"day": "Notaday", "start": "09:00", "end": "17:00"}])

    def test_slot_not_dict_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        with pytest.raises(ValidationError, match="must be an object"):
            update_guide_availability(mock_conn, 1, ["not a dict"])

    def test_existing_pattern_updates_slots(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        pattern_result = MagicMock()
        pattern_result.fetchone.return_value = (100, "UTC")
        # update_guide_availability: guide check, pattern fetch, delete slots, insert slot
        mock_conn.execute.side_effect = [guide_result, pattern_result, MagicMock(), MagicMock()]

        update_guide_availability(mock_conn, 1, [{"day": "Monday", "start": "09:00", "end": "17:00"}])

        assert mock_conn.execute.call_count >= 4
        mock_conn.commit.assert_called_once()

    def test_no_pattern_creates_one_and_inserts_slots(self, mock_conn):
        guide_result = MagicMock()
        guide_result.fetchone.return_value = (1,)
        pattern_result = MagicMock()
        pattern_result.fetchone.return_value = None  # no existing pattern
        insert_result = MagicMock()
        insert_result.fetchone.return_value = (200,)  # new pattern id
        mock_conn.execute.side_effect = [guide_result, pattern_result, insert_result, None, None]

        update_guide_availability(mock_conn, 1, [{"day": "Tuesday", "start": "10:00", "end": "16:00"}])

        mock_conn.commit.assert_called_once()
