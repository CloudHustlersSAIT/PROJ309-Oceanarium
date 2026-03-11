import logging

from fastapi import APIRouter, Depends

from ..db import get_db
from ..services import customer as customer_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("")
def read_customers(conn=Depends(get_db)):
    try:
        return customer_service.list_customers(conn)
    except Exception as e:
        return handle_domain_exception(e)
