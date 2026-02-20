"""Financial metrics calculator - balance, flow, ratios, distribution, trend."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from app.analytics.types import AccountRecord, TransactionRecord


@dataclass
class BalanceSummary:
    """Total and per-account balance."""

    total: float
    by_account: dict[str, float] = field(default_factory=dict)


@dataclass
class MonthlyFlow:
    """Income and expense flow for a month."""

    year: int
    month: int
    income: float
    expense: float
    net: float


@dataclass
class CategoryDistribution:
    """Spending/income distribution by category."""

    by_category: dict[str, float] = field(default_factory=dict)
    total: float = 0.0


@dataclass
class MonthlyTrend:
    """Monthly balance or flow trend."""

    monthly: list[tuple[str, float]] = field(default_factory=list)  # (YYYY-MM, value)
    average: float = 0.0


def total_balance(
    accounts: list[AccountRecord],
    transactions: list[TransactionRecord] | None = None,
) -> float:
    """Total balance from accounts. If transactions given, can override with computed from tx."""
    if transactions:
        return _balance_from_transactions(transactions)
    return sum(a.balance for a in accounts)


def balance_by_account(
    accounts: list[AccountRecord],
    transactions: list[TransactionRecord] | None = None,
) -> dict[str, float]:
    """Balance per account id."""
    result: dict[str, float] = {}
    if transactions:
        for tx in transactions:
            aid = tx.account_id
            if aid not in result:
                result[aid] = 0.0
            if tx.type == "income":
                result[aid] += tx.amount
            else:
                result[aid] -= tx.amount
        return result
    for a in accounts:
        result[a.id] = float(a.balance)
    return result


def _balance_from_transactions(transactions: list[TransactionRecord]) -> float:
    total = 0.0
    for tx in transactions:
        if tx.type == "income":
            total += tx.amount
        else:
            total -= tx.amount
    return total


def monthly_flow(transactions: list[TransactionRecord]) -> list[MonthlyFlow]:
    """Income and expense per month."""
    by_month: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for tx in transactions:
        key = (tx.date.year, tx.date.month)
        if tx.type == "income":
            by_month[key]["income"] += tx.amount
        else:
            by_month[key]["expense"] += tx.amount

    result: list[MonthlyFlow] = []
    for (year, month), vals in sorted(by_month.items()):
        income = vals["income"]
        expense = vals["expense"]
        result.append(
            MonthlyFlow(
                year=year,
                month=month,
                income=income,
                expense=expense,
                net=income - expense,
            )
        )
    return result


def savings_ratio(transactions: list[TransactionRecord], year: int | None = None, month: int | None = None) -> float | None:
    """Savings ratio = (income - expense) / income. Returns None if no income."""
    flow = monthly_flow(transactions)
    if year is not None and month is not None:
        flow = [f for f in flow if f.year == year and f.month == month]
    if not flow:
        return None
    total_income = sum(f.income for f in flow)
    total_expense = sum(f.expense for f in flow)
    if total_income <= 0:
        return None
    return (total_income - total_expense) / total_income


def distribution_by_category(
    transactions: list[TransactionRecord],
    transaction_type: str = "expense",
    year: int | None = None,
    month: int | None = None,
) -> CategoryDistribution:
    """Distribution by category for income or expense."""
    filtered = [
        t for t in transactions
        if t.type == transaction_type
        and (year is None or t.date.year == year)
        and (month is None or t.date.month == month)
    ]
    by_cat: dict[str, float] = defaultdict(float)
    for t in filtered:
        by_cat[t.category] += t.amount
    total = sum(by_cat.values())
    return CategoryDistribution(by_category=dict(by_cat), total=total)


def monthly_trend(
    transactions: list[TransactionRecord],
    metric: str = "net",
) -> MonthlyTrend:
    """Monthly trend of flow (income, expense, or net)."""
    flow = monthly_flow(transactions)
    monthly: list[tuple[str, float]] = []
    for f in flow:
        key = f"{f.year:04d}-{f.month:02d}"
        if metric == "income":
            val = f.income
        elif metric == "expense":
            val = f.expense
        else:
            val = f.net
        monthly.append((key, val))

    avg = sum(v for _, v in monthly) / len(monthly) if monthly else 0.0
    return MonthlyTrend(monthly=monthly, average=avg)
