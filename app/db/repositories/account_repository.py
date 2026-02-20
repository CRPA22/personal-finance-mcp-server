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
