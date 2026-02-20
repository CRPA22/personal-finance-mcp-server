"""Tests for TransactionService."""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models import Account, Transaction
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService


def test_transaction_service_create_success() -> None:
    """create() returns TransactionSchema and updates balance."""
    account_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.balance = 100.0

    transaction = MagicMock(spec=Transaction)
    transaction.id = uuid.uuid4()
    transaction.account_id = account_id
    transaction.amount = 50
    transaction.type = "expense"
    transaction.category = "groceries"
    transaction.date = date(2025, 2, 19)
    transaction.description = None
    transaction.created_at = MagicMock()

    transaction_repo = MagicMock()
    transaction_repo.create.return_value = transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionCreate(
        account_id=account_id,
        amount=50,
        type="expense",
        category="groceries",
        date=date(2025, 2, 19),
    )
    result = service.create(data)

    assert result.amount == 50
    assert result.type == "expense"
    assert result.category == "groceries"
    assert account.balance == 50.0  # 100 - 50
    transaction_repo.create.assert_called_once()


def test_transaction_service_create_income_increases_balance() -> None:
    """create() with type=income increases account balance."""
    account_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.balance = 100.0

    transaction = MagicMock(spec=Transaction)
    transaction.id = uuid.uuid4()
    transaction.account_id = account_id
    transaction.amount = 75
    transaction.type = "income"
    transaction.category = "salary"
    transaction.date = date(2025, 2, 19)
    transaction.description = None
    transaction.created_at = MagicMock()

    transaction_repo = MagicMock()
    transaction_repo.create.return_value = transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionCreate(
        account_id=account_id,
        amount=75,
        type="income",
        category="salary",
        date=date(2025, 2, 19),
    )
    service.create(data)

    assert account.balance == 175.0  # 100 + 75


def test_transaction_service_create_account_not_found() -> None:
    """create() raises NotFoundError when account does not exist."""
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = None

    transaction_repo = MagicMock()
    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionCreate(
        account_id=uuid.uuid4(),
        amount=10,
        type="expense",
        category="test",
        date=date(2025, 2, 19),
    )

    with pytest.raises(NotFoundError, match="Account .* not found"):
        service.create(data)

    transaction_repo.create.assert_not_called()
