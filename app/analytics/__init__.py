"""Analytics engine - independent of MCP."""

from app.analytics.calculator import (
    balance_by_account,
    monthly_flow,
    savings_ratio,
    total_balance,
)
from app.analytics.forecast import forecast_balance
from app.analytics.anomaly import detect_anomalies

__all__ = [
    "total_balance",
    "balance_by_account",
    "monthly_flow",
    "savings_ratio",
    "forecast_balance",
    "detect_anomalies",
]
