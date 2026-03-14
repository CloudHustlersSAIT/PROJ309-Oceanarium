from unittest.mock import MagicMock, patch

import pytest

from app.services.poller_listener import process_staging_rows


def _make_staging_row(
    row_id=1,
    poll_execution_id=100,
    clorian_reservation_id="RSV-001",
    program_id=1001,
    language_code="en",
    event_start="2026-03-10T10:00:00Z",
    status="CONFIRMED",
    old_reservation=None,
):
    """Build a staging row mapping with embedded payload."""
    return {
        "id": row_id,
        "poll_execution_id": poll_execution_id,
        "payload_json": {
            "clorian_reservation_id": clorian_reservation_id,
            "clorian_purchase_id": "PUR-001",
            "language_code": language_code,
            "event_start_datetime": event_start,
            "event_end_datetime": event_start,
            "status": status,
            "current_ticket_num": 2,
            "clorian_created_at": "2026-03-01T00:00:00Z",
            "clorian_modified_at": "2026-03-01T00:00:00Z",
            "tour": {"program_id": program_id},
            "customer": {
                "clorian_client_id": "CLI-001",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
            },
            "tickets": [
                {
                    "clorian_ticket_id": "TKT-001",
                    "buyer_type_id": 1,
                    "buyer_type_name": "Adult",
                    "start_datetime": event_start,
                    "end_datetime": event_start,
                    "ticket_status": "ACTIVE",
                    "price": 25.0,
                    "venue_id": 1,
                    "venue_name": "Main Hall",
                    "clorian_created_at": "2026-03-01T00:00:00Z",
                    "clorian_modified_at": "2026-03-01T00:00:00Z",
                },
            ],
        },
    }


def _build_mock_conn(staging_rows, old_reservation=None, latest_hash=None):
    """Set up a mock conn with the right sequence of execute return values per staging row."""
    conn = MagicMock()

    mappings_result = MagicMock()
    mappings_result.all.return_value = staging_rows
    staging_query_result = MagicMock()
    staging_query_result.mappings.return_value = mappings_result

    execute_returns = [staging_query_result]

    for _ in staging_rows:
        execute_returns.append(MagicMock())  # INSERT customer
        execute_returns.append(_scalar_one(1))  # SELECT customer id
        execute_returns.append(_fetchone((10,)))  # SELECT tour id
        execute_returns.append(_fetchone(old_reservation))  # SELECT old reservation
        execute_returns.append(_fetchone((100,)))  # INSERT/UPSERT reservation RETURNING id
        if old_reservation is None:
            execute_returns.append(MagicMock())  # UPDATE reservations SET schedule_id
        execute_returns.append(MagicMock())  # INSERT ticket

        hash_row = (latest_hash,) if latest_hash else None
        execute_returns.append(_fetchone(hash_row))  # SELECT latest hash
        if not latest_hash or latest_hash != "anything":
            execute_returns.append(MagicMock())  # INSERT reservation_versions

        execute_returns.append(MagicMock())  # UPDATE poll_staging

    conn.execute.side_effect = execute_returns
    return conn


def _scalar_one(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _fetchone(row):
    result = MagicMock()
    result.fetchone.return_value = row
    return result


class TestProcessStagingRows:
    @pytest.fixture(autouse=True)
    def _patch_get_or_create_schedule(self, monkeypatch):
        # Avoid exercising schedule creation logic in these unit tests.
        monkeypatch.setattr(
            "app.services.poller_listener.get_or_create_schedule",
            lambda *args, **kwargs: 1,
        )

    def test_no_rows_returns_zero(self, mock_conn):
        mappings_result = MagicMock()
        mappings_result.all.return_value = []
        query_result = MagicMock()
        query_result.mappings.return_value = mappings_result
        mock_conn.execute.return_value = query_result

        count = process_staging_rows(mock_conn)
        assert count == 0

    def test_create_scenario(self):
        row = _make_staging_row()
        conn = _build_mock_conn([row])
        count = process_staging_rows(conn)
        assert count == 1

    def test_tour_not_found_raises(self, mock_conn):
        row = _make_staging_row()
        mappings_result = MagicMock()
        mappings_result.all.return_value = [row]
        staging_result = MagicMock()
        staging_result.mappings.return_value = mappings_result

        mock_conn.execute.side_effect = [
            staging_result,
            MagicMock(),  # INSERT customer
            _scalar_one(1),  # SELECT customer id
            _fetchone(None),  # SELECT tour id -- NOT FOUND
        ]

        with pytest.raises(Exception, match="Tour not found"):
            process_staging_rows(mock_conn)

    @patch("app.services.poller_listener.dispatch_events")
    @patch("app.services.poller_listener.handle_reservation_cancellation")
    def test_cancellation_detected(self, mock_cancel, mock_dispatch):
        mock_cancel.return_value = {"schedule_id": 50, "affected_guide_id": None, "old_guide_id": None}
        old_row = (100, 10, "en", "2026-03-10T10:00:00Z", "CONFIRMED", 50)
        row = _make_staging_row(status="CANCELLED")
        conn = _build_mock_conn([row], old_reservation=old_row)

        original_side_effect = list(conn.execute.side_effect)
        original_side_effect.insert(9, MagicMock())
        conn.execute.side_effect = original_side_effect

        count = process_staging_rows(conn)
        assert count == 1
        mock_cancel.assert_called_once()
        mock_dispatch.assert_not_called()

    @patch("app.services.poller_listener.dispatch_events")
    @patch("app.services.poller_listener.handle_reservation_change")
    def test_language_change_detected(self, mock_change, mock_dispatch):
        mock_change.return_value = {
            "new_schedule_id": 2,
            "affected_guide_id": None,
            "old_schedule_id": 50,
            "old_guide_id": None,
        }
        old_row = (100, 10, "en", "2026-03-10T10:00:00Z", "CONFIRMED", 50)
        row = _make_staging_row(language_code="pt")
        conn = _build_mock_conn([row], old_reservation=old_row)

        count = process_staging_rows(conn)
        assert count == 1
        mock_change.assert_called_once()
        kwargs = mock_change.call_args[1]
        assert kwargs["new_language_code"] == "pt"
        assert kwargs["old_schedule_id"] == 50
        mock_dispatch.assert_not_called()

    @patch("app.services.poller_listener.handle_reservation_change")
    def test_no_change_when_values_same(self, mock_change):
        old_row = (100, 10, "en", "2026-03-10T10:00:00Z", "CONFIRMED", 50)
        row = _make_staging_row()
        conn = _build_mock_conn([row], old_reservation=old_row)

        count = process_staging_rows(conn)
        assert count == 1
        mock_change.assert_not_called()

    def test_multiple_rows_processed(self):
        rows = [
            _make_staging_row(row_id=1, clorian_reservation_id="RSV-001"),
            _make_staging_row(row_id=2, clorian_reservation_id="RSV-002"),
        ]
        conn = _build_mock_conn(rows)
        count = process_staging_rows(conn)
        assert count == 2
