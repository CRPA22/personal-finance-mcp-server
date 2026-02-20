"""Transaction service - business logic for transactions."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.models import Account
from app.schemas.transaction import TransactionCreate, TransactionSchema


class TransactionService:
    """Service for transaction operations."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        session: Session,
    ) -> None:
        self._transaction_repo = transaction_repo
        self._account_repo = account_repo
        self._session = session

    def create(self, data: TransactionCreate) -> TransactionSchema:
        """Create a new transaction and update account balance."""
        account = self._account_repo.get_by_id(data.account_id)
        if account is None:
            raise NotFoundError(f"Account {data.account_id} not found")

        transaction = self._transaction_repo.create(
            account_id=data.account_id,
            amount=data.amount,
            transaction_type=data.type,
            category=data.category,
            transaction_date=data.date,
            description=data.description,
        )

        # Update account balance
        self._update_balance(account, data.amount, data.type)

        return TransactionSchema.model_validate(transaction)

    def _update_balance(self, account: Account, amount: float, transaction_type: str) -> None:
        """Update account balance based on transaction type."""
        if transaction_type == "income":
            account.balance = float(account.balance) + amount
        else:
            account.balance = float(account.balance) - amount
        self._session.flush()

    def get_by_id(self, transaction_id: uuid.UUID) -> TransactionSchema:
        """Get transaction by id."""
        transaction = self._transaction_repo.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Transaction {transaction_id} not found")
        return TransactionSchema.model_validate(transaction)

    def get_by_account(
        self,
        account_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[TransactionSchema]:
        """Get transactions for an account."""
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        transactions = self._transaction_repo.get_by_account(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
        )
        return [TransactionSchema.model_validate(t) for t in transactions]
