from unittest.mock import MagicMock

import pytest

from app.services.customer import create_customer, list_customers, update_customer
from app.services.exceptions import ConflictError, ValidationError


class TestListCustomers:
    def test_returns_rows_as_dicts(self, mock_conn):
        mock_result = MagicMock()
        mock_result.keys.return_value = ["clorian_client_id", "full_name", "email"]
        mock_result.fetchall.return_value = [("MANUAL-000001", "Ana Costa", "ana@test.com")]
        mock_conn.execute.return_value = mock_result

        rows = list_customers(mock_conn)

        assert len(rows) == 1
        assert rows[0]["full_name"] == "Ana Costa"


class TestCreateCustomer:
    def test_raises_when_first_name_missing(self, mock_conn):
        with pytest.raises(ValidationError, match="first_name"):
            create_customer(mock_conn, "   ", "Costa", "ana@test.com")

    def test_raises_when_last_name_missing(self, mock_conn):
        with pytest.raises(ValidationError, match="last_name"):
            create_customer(mock_conn, "Ana", "   ", "ana@test.com")

    def test_raises_when_email_missing(self, mock_conn):
        with pytest.raises(ValidationError, match="email"):
            create_customer(mock_conn, "Ana", "Costa", "   ")

    def test_raises_on_duplicate_clorian_id(self, mock_conn):
        existing_result = MagicMock()
        existing_result.fetchone.return_value = MagicMock()
        mock_conn.execute.return_value = existing_result

        with pytest.raises(ConflictError, match="already exists"):
            create_customer(mock_conn, "Ana", "Costa", "ana@test.com", "CLI-1")

    def test_generates_manual_id_and_creates_customer(self, mock_conn):
        max_result = MagicMock()
        max_result.scalar.return_value = 1

        candidate_exists_result = MagicMock()
        candidate_exists_result.fetchone.return_value = None

        existing_result = MagicMock()
        existing_result.fetchone.return_value = None

        insert_result = MagicMock()
        insert_result.keys.return_value = ["clorian_client_id", "first_name", "last_name", "email"]
        insert_result.fetchone.return_value = ("MANUAL-000002", "Ana", "Costa", "ana@test.com")

        mock_conn.execute.side_effect = [
            max_result,
            candidate_exists_result,
            existing_result,
            insert_result,
        ]

        result = create_customer(mock_conn, "Ana", "Costa", "ana@test.com")

        assert result["clorian_client_id"] == "MANUAL-000002"
        mock_conn.commit.assert_called_once()


class TestUpdateCustomer:
    def test_returns_none_when_no_fields(self, mock_conn):
        assert update_customer(mock_conn, "MANUAL-000001", {}) is None
        mock_conn.execute.assert_not_called()

    def test_returns_none_when_customer_not_found(self, mock_conn):
        update_result = MagicMock()
        update_result.fetchone.return_value = None
        mock_conn.execute.return_value = update_result

        result = update_customer(mock_conn, "MANUAL-999999", {"first_name": "Ana"})

        assert result is None
        mock_conn.commit.assert_called_once()

    def test_updates_customer_successfully(self, mock_conn):
        update_result = MagicMock()
        update_result.keys.return_value = ["clorian_client_id", "first_name", "last_name", "email"]
        update_result.fetchone.return_value = ("MANUAL-000001", "Ana", "Costa", "ana@test.com")
        mock_conn.execute.return_value = update_result

        result = update_customer(mock_conn, "MANUAL-000001", {"first_name": "Ana"})

        assert result["first_name"] == "Ana"
        mock_conn.commit.assert_called_once()
