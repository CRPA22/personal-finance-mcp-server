"""Analysis tools - analyze_month, forecast_balance, detect_anomalies."""

import json
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


def register_analysis_tools(mcp: FastMCP) -> None:
    """Register analysis tools."""

    @mcp.tool()
    def analyze_month(year: int, month: int, user_id: str | None = None) -> str:
        """Analyze a specific month: flow, expense/income by category, savings ratio.

        Args:
            year: Year (e.g. 2025).
            month: Month 1-12.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with flow, expense_by_category, income_by_category, savings_ratio.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format. Must be a valid UUID.")

        if not 1 <= month <= 12:
            return error_response("month must be between 1 and 12")

        logger.info("analyze_month", extra={"year": year, "month": month, "user_id": str(uid)})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                transaction_repo = TransactionRepository(session)
                user_repo = UserRepository(session)
                service = AnalyticsService(account_repo, transaction_repo, user_repo)
                result = service.analyze_month(uid, year, month)
                # Convert flow dataclass to dict if present
                if result.get("flow"):
                    f = result["flow"]
                    result["flow"] = {
                        "year": f.year,
                        "month": f.month,
                        "income": f.income,
                        "expense": f.expense,
                        "net": f.net,
                    }
                return json.dumps(result)
        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("analyze_month unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def forecast_balance(
        months_ahead: int = 3,
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Forecast balance for the next N months using average monthly net flow.

        Args:
            months_ahead: Number of months to project (default 3).
            account_id: Account UUID. If omitted, forecasts total across all accounts.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with points (period, value) and slope.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format. Must be a valid UUID.")

        aid = None
        if account_id:
            try:
                aid = uuid.UUID(account_id)
            except ValueError:
                return error_response("Invalid account_id format. Must be a valid UUID.")

        logger.info("forecast_balance", extra={"months_ahead": months_ahead, "account_id": account_id})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                transaction_repo = TransactionRepository(session)
                user_repo = UserRepository(session)
                service = AnalyticsService(account_repo, transaction_repo, user_repo)
                result = service.forecast(uid, account_id=aid, months_ahead=months_ahead)
                return result.model_dump_json()
        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("forecast_balance unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def detect_anomalies(
        threshold: float = 3.0,
        account_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Detect anomalous transactions using Z-score. Values beyond mean ± threshold*std are flagged.

        Args:
            threshold: Z-score threshold (default 3.0).
            account_id: Account UUID. If omitted, analyzes all accounts.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with anomalies list, threshold, mean, std.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format. Must be a valid UUID.")

        aid = None
        if account_id:
            try:
                aid = uuid.UUID(account_id)
            except ValueError:
                return error_response("Invalid account_id format. Must be a valid UUID.")

        logger.info("detect_anomalies", extra={"threshold": threshold, "account_id": account_id})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                transaction_repo = TransactionRepository(session)
                user_repo = UserRepository(session)
                service = AnalyticsService(account_repo, transaction_repo, user_repo)
                result = service.detect_anomalies(uid, account_id=aid, threshold=threshold)
                return result.model_dump_json()
        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("detect_anomalies unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
