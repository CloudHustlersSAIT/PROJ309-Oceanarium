from fastapi import HTTPException

from .exceptions import ConflictError, NotFoundError, ValidationError


def handle_domain_exception(e: Exception):
    if isinstance(e, ValidationError):
        raise HTTPException(status_code=400, detail=e.message)

    elif isinstance(e, NotFoundError):
        raise HTTPException(status_code=404, detail=e.message)

    elif isinstance(e, ConflictError):
        raise HTTPException(status_code=409, detail=e.message)

    # Temporary for debugging
    raise HTTPException(status_code=500, detail="Internal server error")
