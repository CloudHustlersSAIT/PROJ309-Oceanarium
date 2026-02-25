from datetime import date

from pydantic import BaseModel


class BookingCreate(BaseModel):
    customer_id: str
    tour_id: int
    date: date
    adult_tickets: int
    child_tickets: int


class BookingReschedule(BaseModel):
    new_date: date
