"""Tests for delete operations."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService


def test_account_service_delete_success() -> None:
    """delete() removes account when it exists."""
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = MagicMock()
    account_repo.delete.return_value = None

    user_repo = MagicMock()
    service = AccountService(account_repo, user_repo)

    aid = uuid.uuid4()
    service.delete(aid)

    account_repo.delete.assert_called_once_with(aid)


def test_account_service_delete_not_found() -> None:
    """delete() raises NotFoundError when account does not exist."""
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = None

    user_repo = MagicMock()
    service = AccountService(account_repo, user_repo)

    with pytest.raises(NotFoundError, match="Account .* not found"):
        service.delete(uuid.uuid4())

    account_repo.delete.assert_not_called()


def test_transaction_service_delete_success_reverts_balance() -> None:
    """delete() reverts account balance for expense."""
    transaction = MagicMock()
    transaction.id = uuid.uuid4()
    transaction.account_id = uuid.uuid4()
    transaction.amount = 50.0
    transaction.type = "expense"

    account = MagicMock()
    account.balance = 100.0

    transaction_repo = MagicMock()
    transaction_repo.get_by_id.return_value = transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    service.delete(transaction.id)

    assert account.balance == 150.0  # 100 + 50 reverted
    transaction_repo.delete.assert_called_once_with(transaction.id)


def test_transaction_service_delete_income_reverts_balance() -> None:
    """delete() reverts account balance for income."""
    transaction = MagicMock()
    transaction.id = uuid.uuid4()
    transaction.account_id = uuid.uuid4()
    transaction.amount = 75.0
    transaction.type = "income"

    account = MagicMock()
    account.balance = 200.0

    transaction_repo = MagicMock()
    transaction_repo.get_by_id.return_value = transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    service.delete(transaction.id)

    assert account.balance == 125.0  # 200 - 75 reverted


def test_transaction_service_delete_not_found() -> None:
    """delete() raises NotFoundError when transaction does not exist."""
    transaction_repo = MagicMock()
    transaction_repo.get_by_id.return_value = None

    account_repo = MagicMock()
    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)

    with pytest.raises(NotFoundError, match="Transaction .* not found"):
        service.delete(uuid.uuid4())

    transaction_repo.delete.assert_not_called()
