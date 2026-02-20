"""Minimal types for analytics - no DB/ORM dependencies."""

from dataclasses import dataclass
from datetime import date


@dataclass
class TransactionRecord:
    """Minimal transaction data for analytics."""

    amount: float
    type: str  # income | expense
    category: str
    date: date
    account_id: str


@dataclass
class AccountRecord:
    """Minimal account data for analytics."""

    id: str
    balance: float
