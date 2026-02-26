from typing import Optional

from pydantic import BaseModel


class ResourceCreate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    quantity_available: Optional[int] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    quantity_available: Optional[int] = None


class ResourceOut(BaseModel):
    id: int
    name: Optional[str] = None
    type: Optional[str] = None
    quantity_available: Optional[int] = None

    model_config = {"from_attributes": True}
