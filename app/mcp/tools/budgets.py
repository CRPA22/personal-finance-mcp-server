"""Budget tools - set_budget, list_budgets, update_budget, delete_budget."""

import json
import uuid
from datetime import date

from fastmcp import FastMCP

from app.core.config import settings
from app.core.exceptions import FinanceMCPError, NotFoundError
from app.utils.errors import error_response
from app.utils.logging import get_logger
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.budget_repository import BudgetRepository
from app.db.repositories.category_repository import CategoryRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.session import session_context
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.services.budget_service import BudgetService

logger = get_logger(__name__)


def _build_service(session) -> BudgetService:
    return BudgetService(
        budget_repo=BudgetRepository(session),
        category_repo=CategoryRepository(session),
        transaction_repo=TransactionRepository(session),
        account_repo=AccountRepository(session),
        session=session,
    )


def register_budget_tools(mcp: FastMCP) -> None:
    """Register budget-related tools."""

    @mcp.tool()
    def set_budget(
        category: str,
        month: str,
        limit_amount: float,
        currency: str = "PEN",
        user_id: str | None = None,
    ) -> str:
        """Create or replace a monthly budget for a spending category.

        Args:
            category: Expense category name (e.g. 'restaurantes', 'supermercado').
            month: Month in YYYY-MM format (e.g. '2026-06').
            limit_amount: Maximum amount to spend this month.
            currency: Currency code (PEN, USD, EUR). Default: PEN.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with budget details including spent, remaining and percent_used.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format.")

        try:
            month_date = date.fromisoformat(f"{month}-01")
        except ValueError:
            return error_response("Invalid month format. Use YYYY-MM (e.g. '2026-06').")

        data = BudgetCreate(category=category, month=month_date, limit_amount=limit_amount, currency=currency)

        try:
            with session_context() as session:
                service = _build_service(session)
                budget = service.create(uid, data)
                return budget.model_dump_json()
        except (NotFoundError, ValueError) as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("set_budget unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def list_budgets(
        month: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """List budgets with real-time spending progress.

        Args:
            month: Filter by month YYYY-MM. Omit for all months.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON array with budgets including spent, remaining and percent_used.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format.")

        month_date = None
        if month:
            try:
                month_date = date.fromisoformat(f"{month}-01")
            except ValueError:
                return error_response("Invalid month format. Use YYYY-MM.")

        try:
            with session_context() as session:
                service = _build_service(session)
                budgets = service.get_by_user(uid, month=month_date)
                return json.dumps([b.model_dump(mode="json") for b in budgets])
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("list_budgets unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def update_budget(
        budget_id: str,
        limit_amount: float | None = None,
        currency: str | None = None,
    ) -> str:
        """Update a budget's limit or currency.

        Args:
            budget_id: Budget UUID.
            limit_amount: New spending limit. Omit to keep current.
            currency: New currency code. Omit to keep current.

        Returns:
            JSON with updated budget.
        """
        try:
            bid = uuid.UUID(budget_id)
        except ValueError:
            return error_response("Invalid budget_id format.")

        data = BudgetUpdate(limit_amount=limit_amount, currency=currency)

        try:
            with session_context() as session:
                service = _build_service(session)
                budget = service.update(bid, data)
                return budget.model_dump_json()
        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("update_budget unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def delete_budget(budget_id: str) -> str:
        """Delete a budget.

        Args:
            budget_id: Budget UUID.

        Returns:
            JSON with success message or error.
        """
        try:
            bid = uuid.UUID(budget_id)
        except ValueError:
            return error_response("Invalid budget_id format.")

        try:
            with session_context() as session:
                service = _build_service(session)
                service.delete(bid)
                return json.dumps({"message": "Budget deleted successfully", "budget_id": budget_id})
        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("delete_budget unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
