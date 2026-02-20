"""Tests for AccountService."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models import Account, User
from app.schemas.account import AccountCreate
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
