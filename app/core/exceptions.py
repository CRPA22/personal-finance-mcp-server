"""Domain and application exceptions."""


class FinanceMCPError(Exception):
    """Base exception for the application."""

    pass


class NotFoundError(FinanceMCPError):
    """Resource not found."""

    pass


class ValidationError(FinanceMCPError):
    """Validation error."""

    pass
