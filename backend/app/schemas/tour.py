from typing import Optional

from pydantic import BaseModel


class TourCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None


class TourUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None


class TourOut(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None

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
