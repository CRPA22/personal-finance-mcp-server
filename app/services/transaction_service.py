"""Transaction service - business logic for transactions."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.categories import TRANSFER_CATEGORY
from app.core.exceptions import NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.models import Account
from app.schemas.transaction import TransactionCreate, TransactionSchema, TransactionUpdate


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
        category: str | None = None,
        transaction_type: str | None = None,
    ) -> list[TransactionSchema]:
        """Get transactions for an account, optionally filtered."""
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        transactions = self._transaction_repo.get_by_account(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
        )
        result = [TransactionSchema.model_validate(t) for t in transactions]
        if category:
            result = [t for t in result if t.category == category]
        if transaction_type:
            result = [t for t in result if t.type == transaction_type]
        return result

    def get_by_user(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
    ) -> list[TransactionSchema]:
        """Get transactions for a user (all accounts or one account), with optional filters."""
        accounts = self._account_repo.get_by_user(user_id)
        if not accounts:
            return []

        if account_id is not None:
            return self.get_by_account(
                account_id, from_date, to_date, category, transaction_type
            )

        account_ids = [a.id for a in accounts]
        transactions = self._transaction_repo.get_by_accounts(
            account_ids, from_date=from_date, to_date=to_date
        )
        result = [TransactionSchema.model_validate(t) for t in transactions]
        if category:
            result = [t for t in result if t.category == category]
        if transaction_type:
            result = [t for t in result if t.type == transaction_type]
        return result

    def update(self, transaction_id: uuid.UUID, data: TransactionUpdate) -> TransactionSchema:
        """Update a transaction and adjust account balance accordingly."""
        transaction = self._transaction_repo.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Transaction {transaction_id} not found")

        account = self._account_repo.get_by_id(transaction.account_id)
        if account is None:
            raise NotFoundError(f"Account {transaction.account_id} not found")

        # Revert old transaction effect on balance
        if transaction.type == "income":
            account.balance = float(account.balance) - float(transaction.amount)
        else:
            account.balance = float(account.balance) + float(transaction.amount)
        self._session.flush()

        # Apply new values (use existing if not provided)
        new_amount = data.amount if data.amount is not None else float(transaction.amount)
        new_type = data.type if data.type is not None else transaction.type
        new_category = data.category if data.category is not None else transaction.category
        new_date = data.date if data.date is not None else transaction.date
        new_description = data.description if data.description is not None else transaction.description

        # Update transaction
        self._transaction_repo.update(
            transaction_id,
            amount=new_amount,
            transaction_type=new_type,
            category=new_category,
            transaction_date=new_date,
            description=new_description,
        )

        # Apply new transaction effect on balance
        self._update_balance(account, new_amount, new_type)

        updated = self._transaction_repo.get_by_id(transaction_id)
        return TransactionSchema.model_validate(updated)

    def delete(self, transaction_id: uuid.UUID) -> None:
        """Delete a transaction and revert account balance."""
        transaction = self._transaction_repo.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Transaction {transaction_id} not found")

        account = self._account_repo.get_by_id(transaction.account_id)
        if account is not None:
            # Revert balance: income was added, expense was subtracted
            if transaction.type == "income":
                account.balance = float(account.balance) - transaction.amount
            else:
                account.balance = float(account.balance) + transaction.amount
            self._session.flush()

        self._transaction_repo.delete(transaction_id)

    def transfer(
        self,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount: float,
        transaction_date: date | None = None,
        description: str | None = None,
    ) -> tuple[TransactionSchema, TransactionSchema]:
        """Transfer money between accounts. Creates expense in source, income in destination."""
        if from_account_id == to_account_id:
            raise ValueError("Source and destination accounts must be different")

        from_account = self._account_repo.get_by_id(from_account_id)
        if from_account is None:
            raise NotFoundError(f"Account {from_account_id} not found")

        to_account = self._account_repo.get_by_id(to_account_id)
        if to_account is None:
            raise NotFoundError(f"Account {to_account_id} not found")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        dt = transaction_date if transaction_date is not None else date.today()
        desc = description or f"Transfer to account {to_account_id}"

        # Expense from source account
        tx_out = self._transaction_repo.create(
            account_id=from_account_id,
            amount=amount,
            transaction_type="expense",
            category=TRANSFER_CATEGORY,
            transaction_date=dt,
            description=desc,
        )
        self._update_balance(from_account, amount, "expense")

        # Income to destination account
        tx_in = self._transaction_repo.create(
            account_id=to_account_id,
            amount=amount,
            transaction_type="income",
            category=TRANSFER_CATEGORY,
            transaction_date=dt,
            description=description or f"Transfer from account {from_account_id}",
        )
        self._update_balance(to_account, amount, "income")

        return (
            TransactionSchema.model_validate(tx_out),
            TransactionSchema.model_validate(tx_in),
        )
