from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.cost import Cost
from ..schemas.cost import CostCreate, CostUpdate

router = APIRouter(prefix="/costs", tags=["Costs"])


@router.get("")
def list_costs(tour_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Cost)
    if tour_id is not None:
        query = query.filter(Cost.tour_id == tour_id)
    return [_cost_to_dict(c) for c in query.all()]


@router.get("/{cost_id}")
def get_cost(cost_id: int, db: Session = Depends(get_db)):
    cost = db.query(Cost).filter(Cost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    return _cost_to_dict(cost)


@router.post("", status_code=201)
def create_cost(payload: CostCreate, db: Session = Depends(get_db)):
    cost = Cost(
        tour_id=payload.tour_id,
        ticket_type=payload.ticket_type,
        price=payload.price,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return _cost_to_dict(cost)


@router.patch("/{cost_id}")
def update_cost(cost_id: int, payload: CostUpdate, db: Session = Depends(get_db)):
    cost = db.query(Cost).filter(Cost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")

    if payload.ticket_type is not None:
        cost.ticket_type = payload.ticket_type
    if payload.price is not None:
        cost.price = payload.price
    if payload.valid_from is not None:
        cost.valid_from = payload.valid_from
    if payload.valid_to is not None:
        cost.valid_to = payload.valid_to

    db.commit()
    db.refresh(cost)
    return _cost_to_dict(cost)


@router.delete("/{cost_id}", status_code=204)
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    cost = db.query(Cost).filter(Cost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    db.delete(cost)
    db.commit()


def _cost_to_dict(cost: Cost) -> dict:
    return {
        "id": cost.id,
        "tour_id": cost.tour_id,
        "ticket_type": cost.ticket_type,
        "price": float(cost.price),
        "valid_from": cost.valid_from.isoformat() if cost.valid_from else None,
        "valid_to": cost.valid_to.isoformat() if cost.valid_to else None,
    }
