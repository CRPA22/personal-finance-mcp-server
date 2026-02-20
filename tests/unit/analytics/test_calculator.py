"""Tests for analytics calculator."""

from datetime import date

import pytest

from app.analytics.calculator import (
    balance_by_account,
    distribution_by_category,
    monthly_flow,
    savings_ratio,
    total_balance,
)
from app.analytics.types import AccountRecord, TransactionRecord


def _tx(amount: float, t: str, category: str, dt: date, account_id: str = "acc1") -> TransactionRecord:
    return TransactionRecord(amount=amount, type=t, category=category, date=dt, account_id=account_id)


def _acc(aid: str, balance: float) -> AccountRecord:
    return AccountRecord(id=aid, balance=balance)


def test_total_balance_from_accounts() -> None:
    """Total balance from accounts only."""
    accounts = [_acc("a1", 100), _acc("a2", 200)]
    assert total_balance(accounts) == 300


def test_total_balance_from_transactions() -> None:
    """Total balance computed from transactions."""
    tx = [
        _tx(100, "income", "salary", date(2025, 1, 15)),
        _tx(30, "expense", "food", date(2025, 1, 20)),
    ]
    assert total_balance([], tx) == 70


def test_balance_by_account() -> None:
    """Balance per account from transactions."""
    tx = [
        _tx(100, "income", "s", date(2025, 1, 1), "a1"),
        _tx(50, "expense", "s", date(2025, 1, 2), "a1"),
        _tx(200, "income", "s", date(2025, 1, 1), "a2"),
    ]
    result = balance_by_account([], tx)
    assert result["a1"] == 50
    assert result["a2"] == 200


def test_monthly_flow() -> None:
    """Monthly flow aggregates income and expense."""
    tx = [
        _tx(100, "income", "s", date(2025, 1, 5)),
        _tx(40, "expense", "food", date(2025, 1, 10)),
        _tx(20, "expense", "transport", date(2025, 1, 15)),
        _tx(80, "income", "s", date(2025, 2, 1)),
    ]
    flow = monthly_flow(tx)
    assert len(flow) == 2
    jan = next(f for f in flow if f.month == 1)
    assert jan.income == 100
    assert jan.expense == 60
    assert jan.net == 40


def test_savings_ratio() -> None:
    """Savings ratio = (income - expense) / income."""
    tx = [
        _tx(100, "income", "s", date(2025, 1, 1)),
        _tx(60, "expense", "s", date(2025, 1, 2)),
    ]
    ratio = savings_ratio(tx)
    assert ratio is not None
    assert abs(ratio - 0.4) < 0.001  # 40%


def test_savings_ratio_no_income() -> None:
    """Savings ratio returns None when no income."""
    tx = [_tx(50, "expense", "s", date(2025, 1, 1))]
    assert savings_ratio(tx) is None


def test_distribution_by_category() -> None:
    """Distribution by category for expenses."""
    tx = [
        _tx(30, "expense", "food", date(2025, 1, 1)),
        _tx(20, "expense", "transport", date(2025, 1, 2)),
        _tx(10, "expense", "food", date(2025, 1, 3)),
    ]
    dist = distribution_by_category(tx, "expense")
    assert dist.by_category["food"] == 40
    assert dist.by_category["transport"] == 20
    assert dist.total == 60

