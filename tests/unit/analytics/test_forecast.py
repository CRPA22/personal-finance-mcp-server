"""Tests for analytics forecast."""

from datetime import date

from app.analytics.forecast import forecast_balance
from app.analytics.types import AccountRecord, TransactionRecord


def _tx(amount: float, t: str, category: str, dt: date, account_id: str = "a1") -> TransactionRecord:
    return TransactionRecord(amount=amount, type=t, category=category, date=dt, account_id=account_id)


def _acc(aid: str, balance: float) -> AccountRecord:
    return AccountRecord(id=aid, balance=balance)


def test_forecast_with_history() -> None:
    """Forecast uses average monthly net as slope."""
    accounts = [_acc("a1", 0)]  # balance from transactions
    tx = [
        _tx(100, "income", "s", date(2025, 1, 1)),
        _tx(60, "expense", "s", date(2025, 1, 2)),
        _tx(100, "income", "s", date(2025, 2, 1)),
        _tx(80, "expense", "s", date(2025, 2, 2)),
    ]
    result = forecast_balance(accounts, tx, months_ahead=2)
    assert len(result.points) == 2
    # Net Jan=40, Feb=20, avg=30. Current from tx: 40+20=60
    # First month: 60+30=90, second: 90+30=120
    assert result.slope == 30.0
    assert result.points[0].value == 90
    assert result.points[1].value == 120


def test_forecast_no_history() -> None:
    """Forecast with no transactions returns current balance."""
    accounts = [_acc("a1", 500)]
    result = forecast_balance(accounts, [], months_ahead=3)
    assert len(result.points) == 3
    assert result.points[0].value == 500
    assert result.points[1].value == 500
    assert result.slope == 0.0
