"""Transaction tools - add_transaction."""

import uuid
from datetime import date

from fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import FinanceMCPError, NotFoundError
from app.utils.errors import error_response
from app.utils.logging import get_logger
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.session import session_context
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService

logger = get_logger(__name__)


def register_transaction_tools(mcp: FastMCP) -> None:
    """Register transaction-related tools."""

    @mcp.tool()
    def add_transaction(
        account_id: str,
        amount: float,
        transaction_type: str,
        category: str,
        transaction_date: str,
        description: str | None = None,
    ) -> str:
        """Add an income or expense transaction to an account.

        Args:
            account_id: Account UUID.
            amount: Positive amount.
            transaction_type: income or expense.
            category: Transaction category (e.g. groceries, salary).
            transaction_date: Date in YYYY-MM-DD format.
            description: Optional description.

        Returns:
            JSON string with created transaction or error message.
        """
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            logger.warning("add_transaction invalid account_id", extra={"account_id": account_id})
            return error_response("Invalid account_id format. Must be a valid UUID.")

        try:
            parsed_date = date.fromisoformat(transaction_date)
        except ValueError:
            logger.warning("add_transaction invalid date", extra={"date": transaction_date})
            return error_response("Invalid date format. Use YYYY-MM-DD.")

        logger.info(
            "add_transaction",
            extra={"account_id": account_id, "amount": amount, "type": transaction_type},
        )

        data = TransactionCreate(
            account_id=aid,
            amount=amount,
            type=transaction_type,
            category=category,
            date=parsed_date,
            description=description,
        )

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                transaction = service.create(data)
                return transaction.model_dump_json()
        except PydanticValidationError as e:
            logger.warning("add_transaction validation failed", extra={"errors": e.errors()})
            return error_response("Validation failed", details=e.errors())
        except NotFoundError as e:
            logger.info("add_transaction not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("add_transaction domain error", extra={"message": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("add_transaction unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
