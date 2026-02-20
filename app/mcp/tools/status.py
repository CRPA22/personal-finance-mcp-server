"""Financial status tool - get_financial_status."""

import uuid

from fastmcp import FastMCP

from app.core.config import settings
from app.core.exceptions import FinanceMCPError, NotFoundError
from app.utils.errors import error_response
from app.utils.logging import get_logger
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_context
from app.services.analytics_service import AnalyticsService

logger = get_logger(__name__)


def register_status_tools(mcp: FastMCP) -> None:
    """Register financial status tools."""

    @mcp.tool()
    def get_financial_status(user_id: str | None = None) -> str:
        """Get aggregated financial status: total balance, by account, savings ratio, monthly flow, category distribution.

        Args:
            user_id: User UUID. If omitted, uses default user (dev only).

        Returns:
            JSON with total_balance, by_account, savings_ratio, monthly_flow, category_distribution.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            logger.warning("get_financial_status invalid user_id", extra={"user_id": user_id})
            return error_response("Invalid user_id format. Must be a valid UUID.")

        logger.info("get_financial_status", extra={"user_id": str(uid)})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                transaction_repo = TransactionRepository(session)
                user_repo = UserRepository(session)
                service = AnalyticsService(account_repo, transaction_repo, user_repo)
                status = service.get_financial_status(uid)
                return status.model_dump_json()
        except NotFoundError as e:
            logger.info("get_financial_status not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("get_financial_status domain error", extra={"message": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("get_financial_status unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
