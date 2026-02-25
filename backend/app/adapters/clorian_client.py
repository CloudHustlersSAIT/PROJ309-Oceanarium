from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List, Optional


@dataclass
class ClorianBooking:
    clorian_booking_id: str
    date: date
    start_time: time
    end_time: time
    required_expertise: Optional[str]
    required_category: Optional[str]
    requested_language_code: Optional[str]


class ClorianClientBase(ABC):
    @abstractmethod
    def fetch_bookings(self, since: Optional[datetime] = None) -> List[ClorianBooking]:
        """Fetch current bookings from Clorian. Returns all active bookings."""
        ...
