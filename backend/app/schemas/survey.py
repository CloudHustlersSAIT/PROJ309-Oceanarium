from typing import Optional

from pydantic import BaseModel


class SurveyCreate(BaseModel):
    customer_id: int
    guide_id: int
    booking_version_id: int
    comment: Optional[str] = None
    rating: int


class SurveyUpdate(BaseModel):
    comment: Optional[str] = None
    rating: Optional[int] = None


class SurveyOut(BaseModel):
    id: int
    customer_id: int
    guide_id: int
    booking_version_id: int
    comment: Optional[str] = None
    rating: int

    model_config = {"from_attributes": True}
