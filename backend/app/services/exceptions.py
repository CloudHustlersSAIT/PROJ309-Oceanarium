class DomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class UnassignableError(DomainError):
    def __init__(self, message: str, reasons: list[str] | None = None):
        self.reasons = reasons or []
        super().__init__(message)
