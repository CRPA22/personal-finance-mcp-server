"""Tests for TransactionService."""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.models import Account, Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
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


def test_transaction_service_update_changes_amount_and_balance() -> None:
    """update() reverts old effect, applies new, returns updated transaction."""
    account_id = uuid.uuid4()
    transaction_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.balance = 50.0  # After original expense of 50

    transaction = MagicMock(spec=Transaction)
    transaction.id = transaction_id
    transaction.account_id = account_id
    transaction.amount = 50.0
    transaction.type = "expense"
    transaction.category = "groceries"
    transaction.date = date(2025, 2, 19)
    transaction.description = "old"

    updated_transaction = MagicMock(spec=Transaction)
    updated_transaction.id = transaction_id
    updated_transaction.account_id = account_id
    updated_transaction.amount = 30.0
    updated_transaction.type = "expense"
    updated_transaction.category = "groceries"
    updated_transaction.date = date(2025, 2, 19)
    updated_transaction.description = "new"
    updated_transaction.created_at = MagicMock()

    transaction_repo = MagicMock()
    transaction_repo.get_by_id.side_effect = [transaction, updated_transaction]
    transaction_repo.update.return_value = updated_transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionUpdate(amount=30.0, description="new")

    result = service.update(transaction_id, data)

    # Revert: 50 + 50 = 100, then apply 30 expense: 100 - 30 = 70
    assert account.balance == 70.0
    assert result.amount == 30.0
    assert result.description == "new"


def test_transaction_service_update_changes_type() -> None:
    """update() changing type from expense to income updates balance correctly."""
    account_id = uuid.uuid4()
    transaction_id = uuid.uuid4()
    account = MagicMock(spec=Account)
    account.id = account_id
    account.balance = 50.0  # Original: 100 - 50 expense

    transaction = MagicMock(spec=Transaction)
    transaction.id = transaction_id
    transaction.account_id = account_id
    transaction.amount = 50.0
    transaction.type = "expense"
    transaction.category = "test"
    transaction.date = date(2025, 2, 19)
    transaction.description = None

    updated_transaction = MagicMock(spec=Transaction)
    updated_transaction.id = transaction_id
    updated_transaction.account_id = account_id
    updated_transaction.amount = 50.0
    updated_transaction.type = "income"
    updated_transaction.category = "test"
    updated_transaction.date = date(2025, 2, 19)
    updated_transaction.description = None
    updated_transaction.created_at = MagicMock()

    transaction_repo = MagicMock()
    transaction_repo.get_by_id.side_effect = [transaction, updated_transaction]
    transaction_repo.update.return_value = updated_transaction

    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionUpdate(type="income")

    result = service.update(transaction_id, data)

    # Revert expense: 50 + 50 = 100; apply income: 100 + 50 = 150
    assert account.balance == 150.0
    assert result.type == "income"


def test_transaction_service_update_not_found() -> None:
    """update() raises NotFoundError when transaction does not exist."""
    transaction_repo = MagicMock()
    transaction_repo.get_by_id.return_value = None
    account_repo = MagicMock()
    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    data = TransactionUpdate(amount=10.0)

    with pytest.raises(NotFoundError, match="Transaction .* not found"):
        service.update(uuid.uuid4(), data)

    transaction_repo.update.assert_not_called()


def test_transaction_service_transfer_success() -> None:
    """transfer() creates expense in source, income in destination, updates both balances."""
    from_account_id = uuid.uuid4()
    to_account_id = uuid.uuid4()
    from_account = MagicMock(spec=Account)
    from_account.id = from_account_id
    from_account.balance = 100.0
    to_account = MagicMock(spec=Account)
    to_account.id = to_account_id
    to_account.balance = 50.0

    tx_out = MagicMock(spec=Transaction)
    tx_out.id = uuid.uuid4()
    tx_out.account_id = from_account_id
    tx_out.amount = 30.0
    tx_out.type = "expense"
    tx_out.category = "transferencia"
    tx_out.date = date(2025, 2, 19)
    tx_out.description = None
    tx_out.created_at = MagicMock()

    tx_in = MagicMock(spec=Transaction)
    tx_in.id = uuid.uuid4()
    tx_in.account_id = to_account_id
    tx_in.amount = 30.0
    tx_in.type = "income"
    tx_in.category = "transferencia"
    tx_in.date = date(2025, 2, 19)
    tx_in.description = None
    tx_in.created_at = MagicMock()

    transaction_repo = MagicMock()
    transaction_repo.create.side_effect = [tx_out, tx_in]

    account_repo = MagicMock()
    account_repo.get_by_id.side_effect = [from_account, to_account]

    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)
    result_out, result_in = service.transfer(from_account_id, to_account_id, 30.0)

    assert result_out.type == "expense"
    assert result_out.amount == 30.0
    assert result_in.type == "income"
    assert result_in.amount == 30.0
    assert from_account.balance == 70.0
    assert to_account.balance == 80.0
    assert transaction_repo.create.call_count == 2


def test_transaction_service_transfer_same_account_raises() -> None:
    """transfer() raises ValueError when source and destination are the same."""
    account_id = uuid.uuid4()
    transaction_repo = MagicMock()
    account_repo = MagicMock()
    session = MagicMock()

    service = TransactionService(transaction_repo, account_repo, session)

    with pytest.raises(ValueError, match="must be different"):
        service.transfer(account_id, account_id, 10.0)

    transaction_repo.create.assert_not_called()
