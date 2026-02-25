from typing import Optional

from pydantic import BaseModel


class TourOut(BaseModel):
    id: int
    clorian_booking_id: str
    date: str
    start_time: str
    end_time: str
    required_expertise: Optional[str]
    required_category: Optional[str]
    requested_language_code: Optional[str]
    status: str
    assigned_guide_id: Optional[int]
    assigned_guide_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ManualAssignIn(BaseModel):
    guide_id: int
    assigned_by: str


class AssignmentLogOut(BaseModel):
    id: int
    tour_id: int
    guide_id: Optional[int]
    assigned_at: str
    assigned_by: Optional[str]
    assignment_type: str
    action: str

    model_config = {"from_attributes": True}


class SyncLogOut(BaseModel):
    id: int
    started_at: str
    finished_at: Optional[str]
    new_count: int
    changed_count: int
    cancelled_count: int
    status: str
    errors: Optional[str]

    model_config = {"from_attributes": True}
