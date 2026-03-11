import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..db import get_db
from ..dependencies.auth import require_authenticated_user
from ..services import customer as customer_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


@router.get("")
def read_customers(conn=Depends(get_db)):
    try:
        return customer_service.list_customers(conn)
    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/{customer_id}")
def edit_customer(
    customer_id: str,
    payload: CustomerUpdate,
    conn=Depends(get_db),
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        updated = customer_service.update_customer(
            conn,
            customer_id,
            payload.model_dump(exclude_none=True),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        return handle_domain_exception(e)
