"""Transaction tools - transfer, list_transactions, get_transaction, add_transaction, edit_transaction, delete_transaction, export_transactions."""

import csv
import io
import json
import uuid
from datetime import date

from fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from app.core.categories import DEFAULT_CATEGORIES
from app.core.config import settings
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
    def transfer(
        from_account_id: str,
        to_account_id: str,
        amount: float,
        transaction_date: str | None = None,
        description: str | None = None,
    ) -> str:
        """Transfer money between two accounts. Creates expense in source, income in destination.

        Args:
            from_account_id: Source account UUID.
            to_account_id: Destination account UUID.
            amount: Amount to transfer (positive).
            transaction_date: Date YYYY-MM-DD. Omit for today.
            description: Optional description for both movements.

        Returns:
            JSON with both transactions (outgoing, incoming) or error.
        """
        try:
            fid = uuid.UUID(from_account_id)
            tid = uuid.UUID(to_account_id)
        except ValueError:
            return error_response("Invalid account_id format. Must be a valid UUID.")

        parsed_date = None
        if transaction_date:
            try:
                parsed_date = date.fromisoformat(transaction_date)
            except ValueError:
                return error_response("Invalid date format. Use YYYY-MM-DD.")

        logger.info("transfer", extra={"from": from_account_id, "to": to_account_id, "amount": amount})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                tx_out, tx_in = service.transfer(
                    fid,
                    tid,
                    amount,
                    transaction_date=parsed_date,
                    description=description,
                )
                return json.dumps({
                    "outgoing": tx_out.model_dump(mode="json"),
                    "incoming": tx_in.model_dump(mode="json"),
                    "message": "Transfer completed successfully",
                })
        except ValueError as e:
            logger.warning("transfer validation error", extra={"detail": str(e)})
            return error_response(str(e))
        except NotFoundError as e:
            logger.info("transfer not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("transfer unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def get_categories(transaction_type: str | None = None) -> str:
        """Get predefined suggested categories for transactions.

        Args:
            transaction_type: 'income' or 'expense'. Omit for both.

        Returns:
            JSON with expense, income and optionally transfer categories.
        """
        if transaction_type:
            if transaction_type not in ("income", "expense"):
                return error_response("transaction_type must be 'income' or 'expense'.")
            result = {transaction_type: DEFAULT_CATEGORIES[transaction_type]}
        else:
            result = {
                **DEFAULT_CATEGORIES,
                "transfer": ["transferencia"],
            }
        return json.dumps(result)

    @mcp.tool()
    def list_transactions(
        account_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """List transactions for an account or all user accounts, with optional filters.

        Args:
            account_id: Account UUID. Omit to list all user accounts.
            from_date: Start date YYYY-MM-DD. Omit for no lower bound.
            to_date: End date YYYY-MM-DD. Omit for no upper bound.
            category: Filter by category (e.g. groceries).
            transaction_type: Filter by income or expense.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON array of transactions or error.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            logger.warning("list_transactions invalid user_id", extra={"user_id": user_id})
            return error_response("Invalid user_id format. Must be a valid UUID.")

        aid = None
        if account_id is not None:
            try:
                aid = uuid.UUID(account_id)
            except ValueError:
                return error_response("Invalid account_id format. Must be a valid UUID.")

        parsed_from = None
        if from_date:
            try:
                parsed_from = date.fromisoformat(from_date)
            except ValueError:
                return error_response("Invalid from_date format. Use YYYY-MM-DD.")
        parsed_to = None
        if to_date:
            try:
                parsed_to = date.fromisoformat(to_date)
            except ValueError:
                return error_response("Invalid to_date format. Use YYYY-MM-DD.")

        logger.info("list_transactions", extra={"account_id": account_id, "user_id": str(uid)})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                transactions = service.get_by_user(
                    uid,
                    account_id=aid,
                    from_date=parsed_from,
                    to_date=parsed_to,
                    category=category,
                    transaction_type=transaction_type,
                )
                return json.dumps([t.model_dump(mode="json") for t in transactions])
        except NotFoundError as e:
            logger.info("list_transactions not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("list_transactions domain error", extra={"detail": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("list_transactions unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def export_transactions(
        format: str = "json",
        account_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Export transactions to CSV or JSON for external use.

        Args:
            format: 'csv' or 'json'. Default: json.
            account_id: Account UUID. Omit for all user accounts.
            from_date: Start date YYYY-MM-DD.
            to_date: End date YYYY-MM-DD.
            category: Filter by category.
            transaction_type: Filter by income or expense.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            CSV or JSON string with transactions.
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

        parsed_from = None
        if from_date:
            try:
                parsed_from = date.fromisoformat(from_date)
            except ValueError:
                return error_response("Invalid from_date format. Use YYYY-MM-DD.")
        parsed_to = None
        if to_date:
            try:
                parsed_to = date.fromisoformat(to_date)
            except ValueError:
                return error_response("Invalid to_date format. Use YYYY-MM-DD.")

        if format.lower() not in ("csv", "json"):
            return error_response("Format must be 'csv' or 'json'.")

        logger.info("export_transactions", extra={"format": format, "user_id": str(uid)})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                transactions = service.get_by_user(
                    uid,
                    account_id=aid,
                    from_date=parsed_from,
                    to_date=parsed_to,
                    category=category,
                    transaction_type=transaction_type,
                )

                if format.lower() == "json":
                    return json.dumps([t.model_dump(mode="json") for t in transactions])

                # CSV export
                if not transactions:
                    return "id,account_id,amount,type,category,date,description,created_at\n"

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["id", "account_id", "amount", "type", "category", "date", "description", "created_at"])
                for t in transactions:
                    writer.writerow([
                        str(t.id),
                        str(t.account_id),
                        t.amount,
                        t.type,
                        t.category,
                        t.date.isoformat() if t.date else "",
                        t.description or "",
                        t.created_at.isoformat() if t.created_at else "",
                    ])
                return output.getvalue()

        except NotFoundError as e:
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("export_transactions unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def get_transaction(transaction_id: str) -> str:
        """Get a single transaction by ID.

        Args:
            transaction_id: Transaction UUID.

        Returns:
            JSON with transaction details or error.
        """
        try:
            tid = uuid.UUID(transaction_id)
        except ValueError:
            logger.warning("get_transaction invalid transaction_id", extra={"transaction_id": transaction_id})
            return error_response("Invalid transaction_id format. Must be a valid UUID.")

        logger.info("get_transaction", extra={"transaction_id": transaction_id})

        try:
            with session_context() as session:
                transaction_repo = TransactionRepository(session)
                account_repo = AccountRepository(session)
                service = TransactionService(
                    transaction_repo,
                    account_repo,
                    session,
                )
                transaction = service.get_by_id(tid)
                return transaction.model_dump_json()
        except NotFoundError as e:
            logger.info("get_transaction not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("get_transaction domain error", extra={"detail": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("get_transaction unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

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
