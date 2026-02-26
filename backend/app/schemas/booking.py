from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

VALID_BOOKING_STATUSES = {"pending", "assigned", "cancelled"}


class BookingVersionCreate(BaseModel):
    status: str = "pending"
    adult_tickets: int = 0
    child_tickets: int = 0
    start_date: date


class BookingCreate(BaseModel):
    clorian_booking_id: str
    customer_id: Optional[int] = None
    tour_id: Optional[int] = None
    status: str = "pending"
    adult_tickets: int = 0
    child_tickets: int = 0
    start_date: date


class BookingReschedule(BaseModel):
    new_date: date


class BookingVersionOut(BaseModel):
    id: int
    booking_id: int
    hash: str
    status: str
    adult_tickets: int
    child_tickets: int
    start_date: date
    received_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    poll_execution_id: Optional[int] = None

    model_config = {"from_attributes": True}


class BookingOut(BaseModel):
    booking_id: int
    clorian_booking_id: str
    customer_id: Optional[int] = None
    tour_id: Optional[int] = None
    created_at: Optional[datetime] = None
    date: Optional[date] = None
    adult_tickets: int = 0
    child_tickets: int = 0
    status: str = "pending"

    model_config = {"from_attributes": True}
