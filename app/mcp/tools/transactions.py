"""Transaction tools - add_transaction, delete_transaction."""

import json
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
from app.schemas.transaction import TransactionCreate, TransactionUpdate
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

    @mcp.tool()
    def edit_transaction(
        transaction_id: str,
        amount: float | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        transaction_date: str | None = None,
        description: str | None = None,
    ) -> str:
        """Edit an existing transaction. Only provided fields are updated.

        Args:
            transaction_id: Transaction UUID to edit.
            amount: New amount (positive). Omit to keep current.
            transaction_type: income or expense. Omit to keep current.
            category: New category. Omit to keep current.
            transaction_date: Date in YYYY-MM-DD. Omit to keep current.
            description: New description. Omit to keep current.

        Returns:
            JSON string with updated transaction or error message.
        """
        try:
            tid = uuid.UUID(transaction_id)
        except ValueError:
            logger.warning("edit_transaction invalid transaction_id", extra={"transaction_id": transaction_id})
            return error_response("Invalid transaction_id format. Must be a valid UUID.")

        parsed_date = None
        if transaction_date is not None:
            try:
                parsed_date = date.fromisoformat(transaction_date)
            except ValueError:
                logger.warning("edit_transaction invalid date", extra={"date": transaction_date})
                return error_response("Invalid date format. Use YYYY-MM-DD.")

        data = TransactionUpdate(
            amount=amount,
            type=transaction_type,
            category=category,
            date=parsed_date,
            description=description,
        )

        logger.info("edit_transaction", extra={"transaction_id": transaction_id})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                transaction = service.update(tid, data)
                return transaction.model_dump_json()
        except PydanticValidationError as e:
            logger.warning("edit_transaction validation failed", extra={"errors": e.errors()})
            return error_response("Validation failed", details=e.errors())
        except NotFoundError as e:
            logger.info("edit_transaction not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("edit_transaction domain error", extra={"message": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("edit_transaction unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def delete_transaction(transaction_id: str) -> str:
        """Delete a transaction and revert its effect on the account balance.

        Args:
            transaction_id: Transaction UUID to delete.

        Returns:
            JSON with success message or error.
        """
        try:
            tid = uuid.UUID(transaction_id)
        except ValueError:
            logger.warning("delete_transaction invalid transaction_id", extra={"transaction_id": transaction_id})
            return error_response("Invalid transaction_id format. Must be a valid UUID.")

        logger.info("delete_transaction", extra={"transaction_id": transaction_id})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                service.delete(tid)
                return json.dumps({"message": "Transaction deleted successfully", "transaction_id": transaction_id})
        except NotFoundError as e:
            logger.info("delete_transaction not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("delete_transaction unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
