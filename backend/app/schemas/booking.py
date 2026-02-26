from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel

VALID_BOOKING_STATUSES = {"unassigned", "assigned", "cancelled"}


class BookingVersionCreate(BaseModel):
    status: str = "unassigned"
    adult_tickets: int = 0
    child_tickets: int = 0
    start_date: date


class BookingCreate(BaseModel):
    clorian_booking_id: str
    customer_id: Optional[int] = None
    tour_id: Optional[int] = None
    status: str = "unassigned"
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
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    received_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    poll_execution_id: Optional[int] = None

    model_config = {"from_attributes": True}


class BookingOut(BaseModel):
    booking_id: int
    clorian_booking_id: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    tour_id: Optional[int] = None
    tour_name: Optional[str] = None
    created_at: Optional[datetime] = None
    date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    adult_tickets: int = 0
    child_tickets: int = 0
    status: str = "unassigned"
    guide_name: Optional[str] = None

    model_config = {"from_attributes": True}
