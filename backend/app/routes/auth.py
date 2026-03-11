from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from ..db import engine
from ..dependencies.auth import require_authenticated_user
from ..services import auth as auth_service
from ..services.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
def get_current_authenticated_user(
    decoded_user: dict = Depends(require_authenticated_user),
):
    try:
        with engine.connect() as conn:
            return auth_service.resolve_authenticated_user(conn, decoded_user)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message) from e

    except NotFoundError as e:
        raise HTTPException(status_code=403, detail=e.message) from e

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to resolve authenticated user",
        ) from None
