from unittest.mock import MagicMock

import pytest

from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.reservation import (
    cancel_reservation,
    create_reservation,
    list_reservations,
)


class TestListReservations:
    def test_returns_rows(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "status"]
        mock_result.fetchall.return_value = [(1, "CONFIRMED"), (2, "CANCELLED")]
        mock_conn.execute.return_value = mock_result

        rows = list_reservations(mock_conn)

        assert len(rows) == 2
        assert rows[0]["id"] == 1


class TestCreateReservation:
    def _payload(self, **overrides):
        defaults = {
            "customer_id": 1,
            "schedule_id": 1,
            "adult_tickets": 2,
            "child_tickets": 0,
            "clorian_reservation_id": None,
            "clorian_purchase_id": None,
            "status": "CONFIRMED",
        }
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_raises_on_negative_tickets(self, mock_conn):
        with pytest.raises(ValidationError, match="negative"):
            create_reservation(mock_conn, self._payload(adult_tickets=-1))

    def test_raises_on_zero_total_tickets(self, mock_conn):
        with pytest.raises(ValidationError, match="At least one ticket"):
            create_reservation(mock_conn, self._payload(adult_tickets=0, child_tickets=0))

    def test_raises_when_customer_not_found(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="Customer not found"):
            create_reservation(mock_conn, self._payload())

    def test_raises_when_schedule_not_found(self, mock_conn):
        customer_result = MagicMock()
        customer_result.fetchone.return_value = MagicMock(id=1)
        schedule_result = MagicMock()
        schedule_result.fetchone.return_value = None
        mock_conn.execute.side_effect = [customer_result, schedule_result]
        with pytest.raises(NotFoundError, match="Schedule not found"):
            create_reservation(mock_conn, self._payload())

    def test_raises_on_duplicate_clorian_id(self, mock_conn):
        from datetime import datetime

        customer_r = MagicMock()
        customer_r.fetchone.return_value = MagicMock(id=1)
        schedule_r = MagicMock()
        schedule_r.fetchone.return_value = MagicMock(
            id=1,
            event_start_datetime=datetime(2026, 1, 1, 10, 0),
            tour_id=1,
            language_code="en",
        )
        dup_r = MagicMock()
        dup_r.fetchone.return_value = MagicMock()
        mock_conn.execute.side_effect = [customer_r, schedule_r, dup_r]
        with pytest.raises(ConflictError, match="clorian_reservation_id"):
            create_reservation(mock_conn, self._payload(clorian_reservation_id="DUP-123"))


class TestCancelReservation:
    def test_raises_when_not_found(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="not found"):
            cancel_reservation(mock_conn, 999)

    def test_raises_when_already_cancelled(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = MagicMock(status="CANCELLED")
        with pytest.raises(ValidationError, match="already cancelled"):
            cancel_reservation(mock_conn, 1)

    def test_successful_cancel(self, mock_conn):
        lookup_result = MagicMock()
        lookup_result.fetchone.return_value = MagicMock(status="CONFIRMED")
        update_result = MagicMock()
        update_result.keys.return_value = ["id", "status"]
        update_result.fetchone.return_value = (1, "CANCELLED")
        mock_conn.execute.side_effect = [lookup_result, update_result]

        result = cancel_reservation(mock_conn, 1)

        assert result["status"] == "CANCELLED"
        mock_conn.commit.assert_called_once()
