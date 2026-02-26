from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.resource import Resource
from ..schemas.resource import ResourceCreate, ResourceUpdate

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("")
def list_resources(db: Session = Depends(get_db)):
    return [_resource_to_dict(r) for r in db.query(Resource).all()]


@router.get("/{resource_id}")
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _resource_to_dict(resource)


@router.post("", status_code=201)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db)):
    resource = Resource(
        name=payload.name,
        type=payload.type,
        quantity_available=payload.quantity_available,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return _resource_to_dict(resource)


@router.patch("/{resource_id}")
def update_resource(resource_id: int, payload: ResourceUpdate, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if payload.name is not None:
        resource.name = payload.name
    if payload.type is not None:
        resource.type = payload.type
    if payload.quantity_available is not None:
        resource.quantity_available = payload.quantity_available

    db.commit()
    db.refresh(resource)
    return _resource_to_dict(resource)


@router.delete("/{resource_id}", status_code=204)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()


def _resource_to_dict(resource: Resource) -> dict:
    return {
        "id": resource.id,
        "name": resource.name,
        "type": resource.type,
        "quantity_available": resource.quantity_available,
    }
