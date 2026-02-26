"""Unit tests for database utility functions."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db import get_db
from app.db import test_connection as db_test_connection


def test_get_db_yields_session():
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_db_connection_returns_value():
    result = db_test_connection()
    assert result is not None


def test_db_connection_handles_failure():
    from unittest.mock import patch

    with patch("app.db.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception("Connection failed")
        result = db_test_connection()
    assert result is None
