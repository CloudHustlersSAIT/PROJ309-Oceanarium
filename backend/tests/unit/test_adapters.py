"""Unit tests for adapters."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import date, time

from app.adapters.clorian_client import ClorianBooking
from app.adapters.clorian_mock import ClorianMockClient


def test_mock_client_default_bookings():
    client = ClorianMockClient()
    bookings = client.fetch_bookings()
    assert len(bookings) == 3
    assert bookings[0].clorian_booking_id == "CLR-001"


def test_mock_client_add_booking():
    client = ClorianMockClient()
    client.clear()
    booking = ClorianBooking(
        clorian_booking_id="CLR-NEW",
        date=date(2026, 4, 1),
        start_time=time(10, 0),
        end_time=time(12, 0),
        required_expertise="Sharks",
        required_category="Marine Biology",
        requested_language_code="en",
    )
    client.add_booking(booking)
    assert len(client.fetch_bookings()) == 1
    assert client.fetch_bookings()[0].clorian_booking_id == "CLR-NEW"


def test_mock_client_remove_booking():
    client = ClorianMockClient()
    initial_count = len(client.fetch_bookings())
    client.remove_booking("CLR-001")
    assert len(client.fetch_bookings()) == initial_count - 1


def test_mock_client_remove_nonexistent_booking():
    client = ClorianMockClient()
    initial_count = len(client.fetch_bookings())
    client.remove_booking("NONEXISTENT")
    assert len(client.fetch_bookings()) == initial_count


def test_mock_client_update_booking():
    client = ClorianMockClient()
    client.update_booking("CLR-001", required_expertise="Dolphins")
    booking = [b for b in client.fetch_bookings() if b.clorian_booking_id == "CLR-001"][0]
    assert booking.required_expertise == "Dolphins"


def test_mock_client_update_nonexistent_booking():
    client = ClorianMockClient()
    client.update_booking("NONEXISTENT", required_expertise="Dolphins")
    bookings = client.fetch_bookings()
    assert len(bookings) == 3


def test_mock_client_clear():
    client = ClorianMockClient()
    assert len(client.fetch_bookings()) > 0
    client.clear()
    assert len(client.fetch_bookings()) == 0


def test_mock_client_fetch_returns_copy():
    client = ClorianMockClient()
    bookings1 = client.fetch_bookings()
    bookings2 = client.fetch_bookings()
    assert bookings1 is not bookings2
