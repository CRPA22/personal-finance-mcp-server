"""Tests for AccountService."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models import Account, User
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.account_service import AccountService


def test_account_service_create_success() -> None:
    """create() returns AccountSchema when user exists."""
    user_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = uuid.uuid4()
    account.user_id = user_id
    account.name = "Test"
    account.type = "checking"
    account.currency = "USD"
    account.balance = 100
    account.created_at = MagicMock()

    account_repo = MagicMock()
    account_repo.create.return_value = account

    user_repo = MagicMock()
    user_repo.get_by_id.return_value = MagicMock(spec=User)

    service = AccountService(account_repo, user_repo)
    data = AccountCreate(
        user_id=user_id,
        name="Test",
        type="checking",
        currency="USD",
        initial_balance=100,
    )
    result = service.create(data)

    assert result.name == "Test"
    assert result.type == "checking"
    assert result.balance == 100
    account_repo.create.assert_called_once()


def test_account_service_create_user_not_found() -> None:
    """create() raises NotFoundError when user does not exist."""
    user_repo = MagicMock()
    user_repo.get_by_id.return_value = None

    account_repo = MagicMock()
    service = AccountService(account_repo, user_repo)

    data = AccountCreate(
        user_id=uuid.uuid4(),
        name="Test",
        type="checking",
    )
    with pytest.raises(NotFoundError, match="User .* not found"):
        service.create(data)

    account_repo.create.assert_not_called()


def test_account_service_adjust_balance_success() -> None:
    """adjust_balance() updates balance and returns updated account."""
    account_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.user_id = uuid.uuid4()
    account.name = "Test"
    account.type = "checking"
    account.currency = "USD"
    account.balance = 100.0
    account.created_at = MagicMock()

    updated_account = MagicMock(spec=Account)
    updated_account.id = account_id
    updated_account.user_id = account.user_id
    updated_account.name = "Test"
    updated_account.type = "checking"
    updated_account.currency = "USD"
    updated_account.balance = 250.0
    updated_account.created_at = account.created_at

    account_repo = MagicMock()
    account_repo.get_by_id.side_effect = [account, updated_account]
    account_repo.update_balance.return_value = updated_account

    user_repo = MagicMock()

    service = AccountService(account_repo, user_repo)
    result = service.adjust_balance(account_id, 250.0)

    assert result.balance == 250.0
    account_repo.update_balance.assert_called_once_with(account_id, 250.0)


def test_account_service_adjust_balance_not_found() -> None:
    """adjust_balance() raises NotFoundError when account does not exist."""
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = None
    user_repo = MagicMock()

    service = AccountService(account_repo, user_repo)

    with pytest.raises(NotFoundError, match="Account .* not found"):
        service.adjust_balance(uuid.uuid4(), 100.0)

    account_repo.update_balance.assert_not_called()


def test_account_service_update_success() -> None:
    """update() changes name, type, currency and returns updated account."""
    account_id = uuid.uuid4()
    user_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.user_id = user_id
    account.name = "Old Name"
    account.type = "checking"
    account.currency = "USD"
    account.balance = 100.0
    account.created_at = MagicMock()

    updated_account = MagicMock(spec=Account)
    updated_account.id = account_id
    updated_account.user_id = user_id
    updated_account.name = "New Name"
    updated_account.type = "savings"
    updated_account.currency = "EUR"
    updated_account.balance = 100.0
    updated_account.created_at = account.created_at

    account_repo = MagicMock()
    account_repo.get_by_id.side_effect = [account, updated_account]

    user_repo = MagicMock()
    service = AccountService(account_repo, user_repo)
    data = AccountUpdate(name="New Name", type="savings", currency="EUR")

    result = service.update(account_id, data)

    assert result.name == "New Name"
    assert result.type == "savings"
    assert result.currency == "EUR"
    account_repo.update.assert_called_once_with(
        account_id, name="New Name", account_type="savings", currency="EUR"
    )
