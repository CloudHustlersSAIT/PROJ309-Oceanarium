from typing import List, Optional

from pydantic import BaseModel


class LanguageOut(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class ExpertiseOut(BaseModel):
    id: int
    name: str
    category: str

    model_config = {"from_attributes": True}


class AvailabilitySlotOut(BaseModel):
    id: int
    day_of_week: int
    start_time: str
    end_time: str

    model_config = {"from_attributes": True}


class AvailabilityExceptionOut(BaseModel):
    id: int
    date: str
    type: str
    reason: Optional[str]

    model_config = {"from_attributes": True}


class AvailabilityPatternOut(BaseModel):
    id: int
    timezone: str
    slots: List[AvailabilitySlotOut] = []
    exceptions: List[AvailabilityExceptionOut] = []

    model_config = {"from_attributes": True}


class GuideOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    languages: List[LanguageOut] = []
    expertises: List[ExpertiseOut] = []
    availability_pattern: Optional[AvailabilityPatternOut] = None

    model_config = {"from_attributes": True}


class ExpertiseIn(BaseModel):
    name: str
    category: str = "General"


class GuideCreate(BaseModel):
    name: str
    email: str
    is_active: bool = True
    languages: List[str] = []
    expertises: List[ExpertiseIn] = []


class GuideUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    languages: Optional[List[str]] = None
    expertises: Optional[List[ExpertiseIn]] = None


class AvailabilitySlotIn(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str


class AvailabilityExceptionIn(BaseModel):
    date: str
    type: str
    reason: Optional[str] = None


class AvailabilitySetIn(BaseModel):
    timezone: str = "UTC"
    slots: List[AvailabilitySlotIn] = []
    exceptions: List[AvailabilityExceptionIn] = []
