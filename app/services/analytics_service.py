"""Analytics service - orchestrates analytics engine with DB data."""

import uuid
from datetime import date

from app.analytics.anomaly import AnomalyResult, detect_anomalies
from app.analytics.calculator import (
    distribution_by_category,
    monthly_flow,
    savings_ratio,
    total_balance,
)
from app.analytics.forecast import forecast_balance
from app.analytics.types import AccountRecord, TransactionRecord
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.analytics import (
    AccountSummaryInStatus,
    AnomaliesSchema,
    AnomalyPointSchema,
    CategoryDistributionSchema,
    FinancialStatusSchema,
    ForecastPointSchema,
    ForecastSchema,
    MonthlyFlowSchema,
)


def _to_transaction_record(tx: object) -> TransactionRecord:
    """Convert ORM/schema to TransactionRecord."""
    return TransactionRecord(
        amount=float(getattr(tx, "amount", 0)),
        type=getattr(tx, "type", "expense"),
        category=getattr(tx, "category", ""),
        date=getattr(tx, "date"),
        account_id=str(getattr(tx, "account_id", "")),
    )


def _to_account_record(acc: object) -> AccountRecord:
    """Convert ORM/schema to AccountRecord."""
    return AccountRecord(
        id=str(getattr(acc, "id", "")),
        balance=float(getattr(acc, "balance", 0)),
    )


class AnalyticsService:
    """Service for financial analytics."""

    def __init__(
        self,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        user_repo: UserRepository,
    ) -> None:
        self._account_repo = account_repo
        self._transaction_repo = transaction_repo
        self._user_repo = user_repo

    def get_financial_status(self, user_id: uuid.UUID) -> FinancialStatusSchema:
        """Get aggregated financial status for a user."""
        accounts = self._account_repo.get_by_user(user_id)
        account_ids = [a.id for a in accounts]
        transactions = self._transaction_repo.get_by_accounts(account_ids)

        acc_records = [_to_account_record(a) for a in accounts]
        tx_records = [_to_transaction_record(t) for t in transactions]

        # Use account balances as source of truth (they're updated by transaction service)
        total = total_balance(acc_records, transactions=None)
        ratio = savings_ratio(tx_records)
        flow = monthly_flow(tx_records)
        dist = distribution_by_category(tx_records, "expense")

        # Build by_account: full account info (id, name, type, currency, balance)
        by_account_list = [
            AccountSummaryInStatus(
                id=str(acc.id),
                name=getattr(acc, "name", ""),
                type=getattr(acc, "type", ""),
                currency=getattr(acc, "currency", "USD"),
                balance=round(float(getattr(acc, "balance", 0)), 2),
            )
            for acc in accounts
        ]

        # Build by_currency: sum balances per currency
        by_currency: dict[str, float] = {}
        for acc in accounts:
            curr = getattr(acc, "currency", "USD")
            bal = float(getattr(acc, "balance", 0))
            by_currency[curr] = by_currency.get(curr, 0) + bal
        by_currency = {k: round(v, 2) for k, v in by_currency.items()}

        return FinancialStatusSchema(
            total_balance=total,
            by_account=by_account_list,
            by_currency=by_currency,
            savings_ratio=round(ratio, 4) if ratio is not None else None,
            monthly_flow=[
                MonthlyFlowSchema(
                    year=f.year,
                    month=f.month,
                    income=round(f.income, 2),
                    expense=round(f.expense, 2),
                    net=round(f.net, 2),
                )
                for f in flow
            ],
            category_distribution=CategoryDistributionSchema(
                by_category=dist.by_category,
                total=round(dist.total, 2),
            ),
        )

    def analyze_month(self, user_id: uuid.UUID, year: int, month: int) -> dict:
        """Analyze a specific month."""
        accounts = self._account_repo.get_by_user(user_id)
        account_ids = [a.id for a in accounts]
        transactions = self._transaction_repo.get_by_accounts(account_ids)

        tx_records = [_to_transaction_record(t) for t in transactions]
        flow = [f for f in monthly_flow(tx_records) if f.year == year and f.month == month]
        dist_expense = distribution_by_category(tx_records, "expense", year, month)
        dist_income = distribution_by_category(tx_records, "income", year, month)
        ratio = savings_ratio(tx_records, year, month)

        return {
            "year": year,
            "month": month,
            "flow": flow[0] if flow else None,
            "expense_by_category": dist_expense.by_category,
            "income_by_category": dist_income.by_category,
            "savings_ratio": ratio,
        }

    def forecast(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
        months_ahead: int = 3,
    ) -> ForecastSchema:
        """Forecast balance for the next N months."""
        accounts = self._account_repo.get_by_user(user_id)
        account_ids = [a.id for a in accounts]
        transactions = self._transaction_repo.get_by_accounts(account_ids)

        acc_records = [_to_account_record(a) for a in accounts]
        tx_records = [_to_transaction_record(t) for t in transactions]

        aid = str(account_id) if account_id else None
        result = forecast_balance(acc_records, tx_records, account_id=aid, months_ahead=months_ahead)

        return ForecastSchema(
            points=[ForecastPointSchema(period=p.period, value=p.value) for p in result.points],
            slope=round(result.slope, 2),
        )

    def detect_anomalies(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
        threshold: float = 3.0,
    ) -> AnomaliesSchema:
        """Detect anomalous transactions using Z-score."""
        accounts = self._account_repo.get_by_user(user_id)
        account_ids = [a.id for a in accounts]
        transactions = self._transaction_repo.get_by_accounts(account_ids)

        tx_records = [_to_transaction_record(t) for t in transactions]
        aid = str(account_id) if account_id else None
        result = detect_anomalies(tx_records, threshold=threshold, account_id=aid)

        return AnomaliesSchema(
            anomalies=[
                AnomalyPointSchema(
                    index=a.index,
                    amount=a.amount,
                    type=a.type,
                    category=a.category,
                    date=a.date,
                    z_score=a.z_score,
                    account_id=a.account_id,
                )
                for a in result.anomalies
            ],
            threshold=result.threshold,
            mean=result.mean,
            std=result.std,
        )
