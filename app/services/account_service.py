"""Account service - business logic for accounts."""

import uuid

from app.core.exceptions import NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.account import AccountCreate, AccountSchema


class AccountService:
    """Service for account operations."""

    def __init__(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ) -> None:
        self._account_repo = account_repo
        self._user_repo = user_repo

    def create(self, data: AccountCreate) -> AccountSchema:
        """Create a new account. Validates user exists."""
        user = self._user_repo.get_by_id(data.user_id)
        if user is None:
            raise NotFoundError(f"User {data.user_id} not found")

        account = self._account_repo.create(
            user_id=data.user_id,
            name=data.name,
            account_type=data.type,
            currency=data.currency,
            balance=data.initial_balance,
        )
        return AccountSchema.model_validate(account)

    def get_by_id(self, account_id: uuid.UUID) -> AccountSchema:
        """Get account by id."""
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")
        return AccountSchema.model_validate(account)

    def get_by_user(self, user_id: uuid.UUID) -> list[AccountSchema]:
        """Get all accounts for a user."""
        accounts = self._account_repo.get_by_user(user_id)
        return [AccountSchema.model_validate(a) for a in accounts]
