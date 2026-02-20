"""Data structures for PDF reports."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class AccountSummary:
    """Account summary for reports."""

    id: str
    name: str
    type: str
    currency: str
    balance: float


@dataclass
class TransactionRow:
    """Transaction row for report tables."""

    date: date
    description: str
    category: str
    amount: float
    account_name: str
    type: str  # income | expense


@dataclass
class CurrencyReportData:
    """Report data grouped by currency."""

    currency: str
    accounts: list[AccountSummary]
    transactions: list[TransactionRow]
    by_category: dict[str, float]
    total_expenses: float
    total_income: float


@dataclass
class ReportContext:
    """Full context for report generation."""

    user_name: str
    from_date: date
    to_date: date
    generated_at: str
    by_currency: dict[str, CurrencyReportData]
    monthly_flow: list[dict]  # [{year, month, income, expense, net}, ...]
    savings_ratio: float | None
