"""Error handling utilities for MCP tools."""

import json
import logging
from typing import Callable, TypeVar

from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import FinanceMCPError, NotFoundError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def error_response(message: str, details: list | dict | None = None) -> str:
    """Build consistent JSON error response."""
    payload: dict = {"error": message}
    if details is not None:
        payload["details"] = details
    return json.dumps(payload)


def handle_tool_errors(
    tool_name: str,
    log_success: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., str]]:
    """Decorator that catches exceptions, logs them, and returns JSON error response."""

    def decorator(fn: Callable[..., T]) -> Callable[..., str]:
        def wrapper(*args: object, **kwargs: object) -> str:
            try:
                result = fn(*args, **kwargs)
                if log_success:
                    logger.info("tool_completed", extra={"tool": tool_name})
                return result
            except PydanticValidationError as e:
                logger.warning(
                    "tool_validation_error",
                    extra={"tool": tool_name, "errors": e.errors()},
                )
                return error_response("Validation failed", details=e.errors())
            except NotFoundError as e:
                logger.info("tool_not_found", extra={"tool": tool_name, "message": str(e)})
                return error_response(str(e))
            except FinanceMCPError as e:
                logger.warning("tool_domain_error", extra={"tool": tool_name, "message": str(e)})
                return error_response(str(e))
            except Exception as e:
                logger.exception(
                    "tool_unexpected_error",
                    extra={"tool": tool_name, "error_type": type(e).__name__},
                )
                return error_response(f"Unexpected error: {e!s}")

        return wrapper

    return decorator
