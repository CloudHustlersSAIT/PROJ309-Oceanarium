"""
Domain exception hierarchy.

Services raise these instead of ``HTTPException`` so that business logic
stays decoupled from HTTP concerns.  The route layer catches them and maps
each type to the appropriate HTTP status code:

- ``ValidationError``  -> 400 Bad Request
- ``NotFoundError``    -> 404 Not Found
- ``ConflictError``    -> 409 Conflict
"""


class DomainError(Exception):
    """Base class for all domain-level errors.

    Every subclass carries a human-readable ``message`` attribute that
    the route layer forwards as the HTTP response detail.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist in the database."""

    pass


class ConflictError(DomainError):
    """Raised when a business rule conflict is detected (e.g., overlapping bookings)."""

    pass


class ValidationError(DomainError):
    """Raised when input data fails domain-level validation rules."""

    pass
