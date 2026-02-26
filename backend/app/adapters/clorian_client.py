from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import List, Optional


@dataclass
class ClorianBooking:
    clorian_booking_id: str
    date: date
    start_time: time
    end_time: time
    required_expertise: Optional[str] = None
    required_category: Optional[str] = None
    requested_language_code: Optional[str] = None
    adult_tickets: int = 0
    child_tickets: int = 0
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    tour_name: Optional[str] = None


class ClorianClientBase(ABC):
    @abstractmethod
    def fetch_bookings(self, since: Optional[datetime] = None) -> List[ClorianBooking]:
        """Fetch current bookings from Clorian. Returns all active bookings."""
        ...
