"""Tests for anomaly detection."""

from datetime import date

from app.analytics.anomaly import detect_anomalies
from app.analytics.types import TransactionRecord


def _tx(amount: float, t: str, category: str, dt: date) -> TransactionRecord:
    return TransactionRecord(amount=amount, type=t, category=category, date=dt, account_id="a1")


def test_detect_anomalies_finds_outlier() -> None:
    """Z-score detects amount far from mean."""
    tx = [
        _tx(10, "expense", "food", date(2025, 1, 1)),
        _tx(12, "expense", "food", date(2025, 1, 2)),
        _tx(11, "expense", "food", date(2025, 1, 3)),
        _tx(5000, "expense", "unknown", date(2025, 1, 4)),  # strong outlier
    ]
    result = detect_anomalies(tx, threshold=1.5)
    assert len(result.anomalies) == 1
    assert result.anomalies[0].amount == 5000
    assert abs(result.anomalies[0].z_score) >= 1.5


def test_detect_anomalies_no_outliers() -> None:
    """No anomalies when all amounts similar."""
    tx = [
        _tx(10, "expense", "f", date(2025, 1, 1)),
        _tx(11, "expense", "f", date(2025, 1, 2)),
        _tx(9, "expense", "f", date(2025, 1, 3)),
    ]
    result = detect_anomalies(tx, threshold=3.0)
    assert len(result.anomalies) == 0


def test_detect_anomalies_insufficient_data() -> None:
    """Returns empty when fewer than 2 transactions."""
    tx = [_tx(100, "expense", "f", date(2025, 1, 1))]
    result = detect_anomalies(tx, threshold=3.0)
    assert len(result.anomalies) == 0
    assert result.mean == 0.0
    assert result.std == 0.0
