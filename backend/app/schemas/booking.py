from datetime import date, time
from typing import Optional

from pydantic import BaseModel

VALID_BOOKING_STATUSES = {"pending", "assigned", "cancelled"}


class BookingCreate(BaseModel):
    clorian_booking_id: str
    date: date
    start_time: time
    end_time: time
    required_expertise: Optional[str] = None
    required_category: Optional[str] = None
    requested_language_code: Optional[str] = None
    customer_id: Optional[str] = None
    adult_tickets: int = 0
    child_tickets: int = 0


class BookingReschedule(BaseModel):
    new_date: date
