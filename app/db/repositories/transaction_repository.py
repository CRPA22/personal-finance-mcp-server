"""Transaction repository."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Transaction


class TransactionRepository:
    """Repository for Transaction CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        amount: float,
        transaction_type: str,
        transaction_date: date,
        description: str | None = None,
        transfer_peer_id: uuid.UUID | None = None,
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            account_id=account_id,
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=transaction_type,
            date=transaction_date,
            description=description,
            transfer_peer_id=transfer_peer_id,
        )
        self._session.add(transaction)
        self._session.flush()
        return transaction

    def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        """Get transaction by id."""
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.id == transaction_id)
        )
        return self._session.scalars(stmt).first()

    def update(
        self,
        transaction_id: uuid.UUID,
        amount: float | None = None,
        transaction_type: str | None = None,
        category_id: uuid.UUID | None = None,
        transaction_date: date | None = None,
        description: str | None = None,
    ) -> Transaction | None:
        """Update a transaction. Returns updated transaction or None if not found."""
        transaction = self.get_by_id(transaction_id)
        if transaction is None:
            return None
        if amount is not None:
            transaction.amount = amount
        if transaction_type is not None:
            transaction.type = transaction_type
        if category_id is not None:
            transaction.category_id = category_id
        if transaction_date is not None:
            transaction.date = transaction_date
        if description is not None:
            transaction.description = description
        self._session.flush()
        return transaction

    def delete(self, transaction_id: uuid.UUID) -> bool:
        """Delete a transaction by id. Returns True if deleted."""
        transaction = self.get_by_id(transaction_id)
        if transaction is None:
            return False
        self._session.delete(transaction)
        self._session.flush()
        return True

    def get_by_account(
        self,
        account_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Transaction]:
        """Get transactions for an account, optionally filtered by date range."""
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.account_id == account_id)
        )
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
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.account_id.in_(account_ids))
        )
        if from_date is not None:
            stmt = stmt.where(Transaction.date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Transaction.date <= to_date)
        stmt = stmt.order_by(Transaction.date.desc())
        return list(self._session.scalars(stmt).unique().all())
