from datetime import date, datetime, time
from typing import List, Optional

from .clorian_client import ClorianBooking, ClorianClientBase


class ClorianMockClient(ClorianClientBase):
    """Mock Clorian client for development and testing.

    Maintains an internal list of bookings that can be manipulated
    in tests via add_booking / remove_booking / update_booking.
    """

    def __init__(self) -> None:
        self._bookings: List[ClorianBooking] = self._default_bookings()

    def fetch_bookings(self, since: Optional[datetime] = None) -> List[ClorianBooking]:
        return list(self._bookings)

    def add_booking(self, booking: ClorianBooking) -> None:
        self._bookings.append(booking)

    def remove_booking(self, clorian_booking_id: str) -> None:
        self._bookings = [
            b for b in self._bookings if b.clorian_booking_id != clorian_booking_id
        ]

    def update_booking(self, clorian_booking_id: str, **kwargs) -> None:
        for b in self._bookings:
            if b.clorian_booking_id == clorian_booking_id:
                for key, value in kwargs.items():
                    setattr(b, key, value)
                break

    def clear(self) -> None:
        self._bookings.clear()

    @staticmethod
    def _default_bookings() -> List[ClorianBooking]:
        return [
            ClorianBooking(
                clorian_booking_id="CLR-001",
                date=date(2026, 3, 2),
                start_time=time(9, 0),
                end_time=time(11, 0),
                required_expertise="Sharks",
                required_category="Marine Biology",
                requested_language_code="en",
            ),
            ClorianBooking(
                clorian_booking_id="CLR-002",
                date=date(2026, 3, 2),
                start_time=time(14, 0),
                end_time=time(16, 0),
                required_expertise="Dolphins",
                required_category="Marine Biology",
                requested_language_code="pt",
            ),
            ClorianBooking(
                clorian_booking_id="CLR-003",
                date=date(2026, 3, 3),
                start_time=time(10, 0),
                end_time=time(12, 0),
                required_expertise="Coral Reef",
                required_category="Marine Ecology",
                requested_language_code="en",
            ),
        ]
