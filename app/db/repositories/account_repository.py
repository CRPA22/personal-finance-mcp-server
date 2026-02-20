"""Account repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account


class AccountRepository:
    """Repository for Account CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        user_id: uuid.UUID,
        name: str,
        account_type: str,
        currency: str = "USD",
        balance: float = 0,
    ) -> Account:
        """Create a new account."""
        account = Account(
            user_id=user_id,
            name=name,
            type=account_type,
            currency=currency,
            balance=float(balance),
        )
        self._session.add(account)
        self._session.flush()
        return account

    def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        """Get account by id."""
        stmt = select(Account).where(Account.id == account_id)
        return self._session.scalars(stmt).first()

    def get_by_user(self, user_id: uuid.UUID) -> list[Account]:
        """Get all accounts for a user."""
        stmt = select(Account).where(Account.user_id == user_id).order_by(Account.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def update(
        self,
        account_id: uuid.UUID,
        name: str | None = None,
        account_type: str | None = None,
        currency: str | None = None,
    ) -> Account | None:
        """Update account fields. Returns account or None if not found."""
        account = self.get_by_id(account_id)
        if account is None:
            return None
        if name is not None:
            account.name = name
        if account_type is not None:
            account.type = account_type
        if currency is not None:
            account.currency = currency
        self._session.flush()
        return account

    def update_balance(self, account_id: uuid.UUID, new_balance: float) -> Account | None:
        """Set account balance to new_balance. Returns account or None if not found."""
        account = self.get_by_id(account_id)
        if account is None:
            return None
        account.balance = float(new_balance)
        self._session.flush()
        return account

    def delete(self, account_id: uuid.UUID) -> bool:
        """Delete an account by id. Transactions are cascade-deleted. Returns True if deleted."""
        account = self.get_by_id(account_id)
        if account is None:
            return False
        self._session.delete(account)
        self._session.flush()
        return True
