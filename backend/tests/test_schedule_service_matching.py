from unittest.mock import MagicMock

from app.services.schedule_service import get_or_create_schedule


def _fetchone(row):
    result = MagicMock()
    result.fetchone.return_value = row
    return result


def test_reuses_existing_active_schedule(mock_conn):
    mock_conn.execute.return_value = _fetchone((77,))

    schedule_id = get_or_create_schedule(
        conn=mock_conn,
        tour_id=2,
        language_code="en",
        event_start_datetime="2026-03-27T09:00:00Z",
        event_end_datetime="2026-03-27T10:00:00Z",
    )

    assert schedule_id == 77
    assert mock_conn.execute.call_count == 1


def test_does_not_reuse_cancelled_schedule_and_creates_new(mock_conn):
    insert_result = _fetchone((88,))
    mock_conn.execute.side_effect = [
        _fetchone(None),
        insert_result,
    ]

    schedule_id = get_or_create_schedule(
        conn=mock_conn,
        tour_id=20,
        language_code="zh",
        event_start_datetime="2026-03-27T09:00:00Z",
        event_end_datetime="2026-03-27T10:00:00Z",
    )

    assert schedule_id == 88
    assert mock_conn.execute.call_count == 2

    select_stmt = str(mock_conn.execute.call_args_list[0].args[0])
    assert "status IN ('UNASSIGNED', 'ASSIGNED', 'CONFIRMED', 'UNASSIGNABLE')" in select_stmt
