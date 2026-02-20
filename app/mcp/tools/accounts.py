"""Account tools - create_account, list_accounts, edit_account."""

import json
import uuid

from fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.exceptions import FinanceMCPError, NotFoundError
from app.utils.errors import error_response
from app.utils.logging import get_logger
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_context
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.account_service import AccountService


logger = get_logger(__name__)


def register_account_tools(mcp: FastMCP) -> None:
    """Register account-related tools."""

    @mcp.tool()
    def list_accounts(user_id: str | None = None) -> str:
        """List all accounts for a user with name, type, currency and balance.

        Args:
            user_id: User UUID. If omitted, uses default user (dev only).

        Returns:
            JSON array of accounts (id, name, type, currency, balance, created_at) or error.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            logger.warning("list_accounts invalid user_id", extra={"user_id": user_id})
            return error_response("Invalid user_id format. Must be a valid UUID.")

        logger.info("list_accounts", extra={"user_id": str(uid)})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                user_repo = UserRepository(session)
                service = AccountService(account_repo, user_repo)
                accounts = service.get_by_user(uid)
                return json.dumps([a.model_dump(mode="json") for a in accounts])
        except NotFoundError as e:
            logger.info("list_accounts not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("list_accounts domain error", extra={"detail": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("list_accounts unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def create_account(
        name: str,
        account_type: str,
        currency: str = "USD",
        initial_balance: float = 0,
        user_id: str | None = None,
    ) -> str:
        """Create a new financial account (checking, savings, or investment).

        Args:
            name: Account display name.
            account_type: One of: checking, savings, investment.
            currency: ISO 4217 code (e.g. USD). Default: USD.
            initial_balance: Starting balance. Default: 0.
            user_id: User UUID. If omitted, uses default user (dev only).

        Returns:
            JSON string with created account or error message.
        """
        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            logger.warning("create_account invalid user_id", extra={"user_id": user_id})
            return error_response("Invalid user_id format. Must be a valid UUID.")

        logger.info("create_account", extra={"account_name": name, "account_type": account_type, "user_id": str(uid)})

        data = AccountCreate(
            user_id=uid,
            name=name,
            type=account_type,
            currency=currency,
            initial_balance=initial_balance,
        )

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                user_repo = UserRepository(session)
                service = AccountService(account_repo, user_repo)
                account = service.create(data)
                return account.model_dump_json()
        except PydanticValidationError as e:
            logger.warning("create_account validation failed", extra={"errors": e.errors()})
            return error_response("Validation failed", details=e.errors())
        except NotFoundError as e:
            logger.info("create_account not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("create_account domain error", extra={"message": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("create_account unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def edit_account(
        account_id: str,
        name: str | None = None,
        account_type: str | None = None,
        currency: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Edit an existing account. Only provided fields are updated.

        Args:
            account_id: Account UUID to edit.
            name: New display name. Omit to keep current.
            account_type: checking, savings or investment. Omit to keep current.
            currency: ISO 4217 code (e.g. USD). Omit to keep current.
            user_id: User UUID (for auth context). Omit to use default user.

        Returns:
            JSON string with updated account or error message.
        """
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            logger.warning("edit_account invalid account_id", extra={"account_id": account_id})
            return error_response("Invalid account_id format. Must be a valid UUID.")

        data = AccountUpdate(name=name, type=account_type, currency=currency)
        logger.info("edit_account", extra={"account_id": account_id})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                user_repo = UserRepository(session)
                service = AccountService(account_repo, user_repo)
                account = service.update(aid, data)
                return account.model_dump_json()
        except PydanticValidationError as e:
            logger.warning("edit_account validation failed", extra={"errors": e.errors()})
            return error_response("Validation failed", details=e.errors())
        except NotFoundError as e:
            logger.info("edit_account not found", extra={"detail": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("edit_account domain error", extra={"detail": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("edit_account unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def adjust_account_balance(account_id: str, new_balance: float) -> str:
        """Set an account's balance to a new value (manual adjustment).

        Args:
            account_id: Account UUID to adjust.
            new_balance: New balance value.

        Returns:
            JSON string with updated account or error message.
        """
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            logger.warning("adjust_account_balance invalid account_id", extra={"account_id": account_id})
            return error_response("Invalid account_id format. Must be a valid UUID.")

        logger.info("adjust_account_balance", extra={"account_id": account_id, "new_balance": new_balance})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                user_repo = UserRepository(session)
                service = AccountService(account_repo, user_repo)
                account = service.adjust_balance(aid, new_balance)
                return account.model_dump_json()
        except NotFoundError as e:
            logger.info("adjust_account_balance not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            logger.warning("adjust_account_balance domain error", extra={"message": str(e)})
            return error_response(str(e))
        except Exception as e:
            logger.exception("adjust_account_balance unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")

    @mcp.tool()
    def delete_account(account_id: str, user_id: str | None = None) -> str:
        """Delete an account and all its transactions.

        Args:
            account_id: Account UUID to delete.
            user_id: User UUID. If omitted, uses default user.

        Returns:
            JSON with success message or error.
        """
        try:
            aid = uuid.UUID(account_id)
        except ValueError:
            logger.warning("delete_account invalid account_id", extra={"account_id": account_id})
            return error_response("Invalid account_id format. Must be a valid UUID.")

        try:
            uid = uuid.UUID(user_id) if user_id else uuid.UUID(settings.default_user_id)
        except ValueError:
            return error_response("Invalid user_id format. Must be a valid UUID.")

        logger.info("delete_account", extra={"account_id": account_id, "user_id": str(uid)})

        try:
            with session_context() as session:
                account_repo = AccountRepository(session)
                user_repo = UserRepository(session)
                service = AccountService(account_repo, user_repo)
                service.delete(aid)
                return json.dumps({"message": "Account deleted successfully", "account_id": account_id})
        except NotFoundError as e:
            logger.info("delete_account not found", extra={"message": str(e)})
            return error_response(str(e))
        except FinanceMCPError as e:
            return error_response(str(e))
        except Exception as e:
            logger.exception("delete_account unexpected error", extra={"error_type": type(e).__name__})
            return error_response(f"Unexpected error: {e!s}")
