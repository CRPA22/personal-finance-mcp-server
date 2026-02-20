"""Report service - gathers data for PDF reports."""

import uuid
from collections import defaultdict
from datetime import date, datetime
from typing import TYPE_CHECKING

from app.core.exceptions import NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.repositories.user_repository import UserRepository

from app.reports.report_data import (
    AccountSummary,
    CurrencyReportData,
    ReportContext,
    TransactionRow,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ReportService:
    """Service for gathering report data."""

    def __init__(
        self,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        user_repo: UserRepository,
    ) -> None:
        self._account_repo = account_repo
        self._transaction_repo = transaction_repo
        self._user_repo = user_repo

    def get_report_data(
        self,
        user_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> ReportContext:
        """Gather all data needed for reports, grouped by currency."""
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")

        user_name = getattr(user, "email", "Usuario")

        accounts = self._account_repo.get_by_user(user_id)
        account_ids = [a.id for a in accounts]

        account_map: dict[uuid.UUID, tuple[str, str]] = {}
        for acc in accounts:
            account_map[acc.id] = (
                getattr(acc, "name", "Cuenta"),
                getattr(acc, "currency", "USD"),
            )

        transactions = self._transaction_repo.get_by_accounts(
            account_ids, from_date=from_date, to_date=to_date
        )

        # Group by currency
        by_currency: dict[str, CurrencyReportData] = {}

        # Accounts per currency
        for acc in accounts:
            curr = getattr(acc, "currency", "USD")
            if curr not in by_currency:
                by_currency[curr] = CurrencyReportData(
                    currency=curr,
                    accounts=[],
                    transactions=[],
                    by_category={},
                    total_expenses=0.0,
                    total_income=0.0,
                )
            by_currency[curr].accounts.append(
                AccountSummary(
                    id=str(acc.id),
                    name=getattr(acc, "name", ""),
                    type=getattr(acc, "type", ""),
                    currency=curr,
                    balance=round(float(getattr(acc, "balance", 0)), 2),
                )
            )

        # Transactions per currency (via account)
        by_category_per_curr: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for tx in transactions:
            acc_id = tx.account_id
            name, curr = account_map.get(acc_id, ("?", "USD"))

            row = TransactionRow(
                date=tx.date,
                description=tx.description or "",
                category=tx.category,
                amount=float(tx.amount),
                account_name=name,
                type=getattr(tx, "type", "expense"),
            )

            if curr not in by_currency:
                by_currency[curr] = CurrencyReportData(
                    currency=curr,
                    accounts=[],
                    transactions=[],
                    by_category={},
                    total_expenses=0.0,
                    total_income=0.0,
                )

            by_currency[curr].transactions.append(row)

            if tx.type == "income":
                by_currency[curr].total_income += float(tx.amount)
            else:
                by_currency[curr].total_expenses += float(tx.amount)
                by_category_per_curr[curr][tx.category] += float(tx.amount)

        for curr, data in by_currency.items():
            data.by_category = dict(by_category_per_curr[curr])
            data.transactions.sort(key=lambda t: t.date)

        # Monthly flow (from transactions)
        monthly: dict[tuple[int, int], dict[str, float]] = defaultdict(
            lambda: {"income": 0.0, "expense": 0.0, "net": 0.0}
        )
        for tx in transactions:
            key = (tx.date.year, tx.date.month)
            if tx.type == "income":
                monthly[key]["income"] += float(tx.amount)
            else:
                monthly[key]["expense"] += float(tx.amount)

        for key, v in monthly.items():
            v["net"] = v["income"] - v["expense"]

        monthly_flow = []
        for (y, m), v in sorted(monthly.items()):
            if from_date <= date(y, m, 1) <= to_date or from_date <= date(y, m, 28) <= to_date:
                monthly_flow.append({
                    "year": y,
                    "month": m,
                    "income": round(v["income"], 2),
                    "expense": round(v["expense"], 2),
                    "net": round(v["net"], 2),
                })

        # Savings ratio
        total_income = sum(d.total_income for d in by_currency.values())
        total_expense = sum(d.total_expenses for d in by_currency.values())
        savings_ratio = None
        if total_income > 0:
            savings_ratio = round((total_income - total_expense) / total_income, 4)

        return ReportContext(
            user_name=user_name,
            from_date=from_date,
            to_date=to_date,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            by_currency=dict(by_currency),
            monthly_flow=monthly_flow,
            savings_ratio=savings_ratio,
        )
