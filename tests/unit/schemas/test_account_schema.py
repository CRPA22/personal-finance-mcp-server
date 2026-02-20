"""Tests for AccountCreate schema validation."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.account import AccountCreate


def test_account_create_valid() -> None:
    """Valid AccountCreate passes."""
    data = AccountCreate(
        user_id=uuid.uuid4(),
        name="Main Checking",
        type="checking",
        currency="USD",
        initial_balance=100.50,
    )
    assert data.name == "Main Checking"
    assert data.type == "checking"
    assert data.initial_balance == 100.50


def test_account_create_defaults() -> None:
    """Defaults apply correctly."""
    data = AccountCreate(
        user_id=uuid.uuid4(),
        name="Savings",
        type="savings",
    )
    assert data.currency == "USD"
    assert data.initial_balance == 0


def test_account_create_invalid_type() -> None:
    """Invalid account type raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        AccountCreate(
            user_id=uuid.uuid4(),
            name="Test",
            type="invalid",
        )
    errors = exc_info.value.errors()
    assert any("pattern" in str(e.get("type", "")) or "literal" in str(e.get("type", "")) for e in errors)


def test_account_create_empty_name() -> None:
    """Empty name raises ValidationError."""
    with pytest.raises(ValidationError):
        AccountCreate(
            user_id=uuid.uuid4(),
            name="",
            type="checking",
        )
