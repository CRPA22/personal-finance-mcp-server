"""Tests for TransactionCreate schema validation."""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate


def test_transaction_create_valid() -> None:
    """Valid TransactionCreate passes."""
    data = TransactionCreate(
        account_id=uuid.uuid4(),
        amount=50.25,
        type="expense",
        category="groceries",
        date=date(2025, 2, 19),
    )
    assert data.amount == 50.25
    assert data.type == "expense"
    assert data.date == date(2025, 2, 19)


def test_transaction_create_with_description() -> None:
    """Optional description accepted."""
    data = TransactionCreate(
        account_id=uuid.uuid4(),
        amount=100,
        type="income",
        category="salary",
        date=date(2025, 2, 19),
        description="Monthly pay",
    )
    assert data.description == "Monthly pay"


def test_transaction_create_invalid_type() -> None:
    """Invalid transaction type raises ValidationError."""
    with pytest.raises(ValidationError):
        TransactionCreate(
            account_id=uuid.uuid4(),
            amount=10,
            type="transfer",
            category="test",
            date=date(2025, 2, 19),
        )


def test_transaction_create_negative_amount() -> None:
    """Negative amount raises ValidationError."""
    with pytest.raises(ValidationError):
        TransactionCreate(
            account_id=uuid.uuid4(),
            amount=-10,
            type="expense",
            category="test",
            date=date(2025, 2, 19),
        )
