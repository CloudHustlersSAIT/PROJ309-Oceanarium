from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    booking_version_id: int
    guide_id: int
    resource_id: Optional[int] = None
    start_date: datetime
    end_date: datetime


class ScheduleUpdate(BaseModel):
    guide_id: Optional[int] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ScheduleOut(BaseModel):
    id: int
    booking_version_id: int
    guide_id: int
    resource_id: Optional[int] = None
    start_date: datetime
    end_date: datetime

    model_config = {"from_attributes": True}
