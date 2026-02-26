from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CostCreate(BaseModel):
    tour_id: int
    ticket_type: str
    price: float
    valid_from: datetime
    valid_to: datetime


class CostUpdate(BaseModel):
    ticket_type: Optional[str] = None
    price: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class CostOut(BaseModel):
    id: int
    tour_id: int
    ticket_type: str
    price: float
    valid_from: datetime
    valid_to: datetime

    model_config = {"from_attributes": True}
