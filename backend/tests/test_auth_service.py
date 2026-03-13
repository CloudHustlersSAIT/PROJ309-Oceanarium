from unittest.mock import MagicMock

import pytest

from app.services.auth import resolve_authenticated_user
from app.services.exceptions import NotFoundError, ValidationError


class TestResolveAuthenticatedUser:
    def test_raises_when_email_missing(self, mock_conn):
        with pytest.raises(ValidationError, match="email"):
            resolve_authenticated_user(mock_conn, {"uid": "u1", "email": ""})

    def test_raises_when_email_blank(self, mock_conn):
        with pytest.raises(ValidationError, match="email"):
            resolve_authenticated_user(mock_conn, {"uid": "u1"})

    def test_returns_admin_when_active(self, mock_conn):
        admin_row = MagicMock(id=1, role="admin", is_active=True)
        mock_conn.execute.return_value.fetchone.return_value = admin_row

        result = resolve_authenticated_user(mock_conn, {"uid": "u1", "email": "admin@test.com"})

        assert result["role"] == "admin"
        assert result["user_id"] == 1
        assert result["guide_id"] is None
        assert result["email"] == "admin@test.com"

    def test_raises_when_admin_inactive(self, mock_conn):
        admin_row = MagicMock(id=1, role="admin", is_active=False)
        mock_conn.execute.return_value.fetchone.return_value = admin_row

        with pytest.raises(ValidationError, match="inactive"):
            resolve_authenticated_user(mock_conn, {"uid": "u1", "email": "admin@test.com"})

    def test_returns_guide_when_active(self, mock_conn):
        admin_result = MagicMock()
        admin_result.fetchone.return_value = None

        guide_row = MagicMock(id=5, first_name="Ana", last_name="Costa")
        guide_result = MagicMock()
        guide_result.fetchone.return_value = guide_row

        mock_conn.execute.side_effect = [admin_result, guide_result]

        result = resolve_authenticated_user(mock_conn, {"uid": "u2", "email": "guide@test.com"})

        assert result["role"] == "guide"
        assert result["guide_id"] == 5
        assert result["user_id"] is None
        assert result["first_name"] == "Ana"

    def test_raises_when_no_matching_role(self, mock_conn):
        admin_result = MagicMock()
        admin_result.fetchone.return_value = None
        guide_result = MagicMock()
        guide_result.fetchone.return_value = None
        mock_conn.execute.side_effect = [admin_result, guide_result]

        with pytest.raises(NotFoundError, match="not mapped"):
            resolve_authenticated_user(mock_conn, {"uid": "u3", "email": "nobody@test.com"})

    def test_non_admin_user_falls_through_to_guide_check(self, mock_conn):
        user_row = MagicMock(id=1, role="viewer", is_active=True)
        admin_result = MagicMock()
        admin_result.fetchone.return_value = user_row

        guide_result = MagicMock()
        guide_result.fetchone.return_value = None

        mock_conn.execute.side_effect = [admin_result, guide_result]

        with pytest.raises(NotFoundError, match="not mapped"):
            resolve_authenticated_user(mock_conn, {"uid": "u4", "email": "viewer@test.com"})
