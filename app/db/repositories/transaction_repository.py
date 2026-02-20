"""Transaction repository."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction


class TransactionRepository:
    """Repository for Transaction CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        account_id: uuid.UUID,
        amount: float,
        transaction_type: str,
        category: str,
        transaction_date: date,
        description: str | None = None,
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            account_id=account_id,
            amount=amount,
            type=transaction_type,
            category=category,
            date=transaction_date,
            description=description,
        )
        self._session.add(transaction)
        self._session.flush()
        return transaction

    def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        """Get transaction by id."""
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        return self._session.scalars(stmt).first()

    def get_by_account(
        self,
        account_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Transaction]:
        """Get transactions for an account, optionally filtered by date range."""
        stmt = select(Transaction).where(Transaction.account_id == account_id)

        if from_date is not None:
            stmt = stmt.where(Transaction.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Transaction.date <= to_date)

        stmt = stmt.order_by(Transaction.date.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_accounts(
        self,
        account_ids: list[uuid.UUID],
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Transaction]:
        """Get transactions for multiple accounts."""
        if not account_ids:
            return []
        stmt = select(Transaction).where(Transaction.account_id.in_(account_ids))
        if from_date is not None:
            stmt = stmt.where(Transaction.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Transaction.date <= to_date)
        stmt = stmt.order_by(Transaction.date.desc())
        return list(self._session.scalars(stmt).all())
