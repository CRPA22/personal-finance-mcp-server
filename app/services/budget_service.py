"""Budget service."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.repositories.account_repository import AccountRepository
from app.db.repositories.budget_repository import BudgetRepository
from app.db.repositories.category_repository import CategoryRepository
from app.db.repositories.transaction_repository import TransactionRepository
from app.schemas.budget import BudgetCreate, BudgetSchema, BudgetUpdate


class BudgetService:
    """Service for budget operations."""

    def __init__(
        self,
        budget_repo: BudgetRepository,
        category_repo: CategoryRepository,
        transaction_repo: TransactionRepository,
        account_repo: AccountRepository,
        session: Session,
    ) -> None:
        self._budget_repo = budget_repo
        self._category_repo = category_repo
        self._transaction_repo = transaction_repo
        self._account_repo = account_repo
        self._session = session

    def _compute_spent(self, budget, account_ids: list[uuid.UUID]) -> float:
        """Calculate how much was spent in the budget's category and month."""
        month_start = budget.month.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        transactions = self._transaction_repo.get_by_accounts(
            account_ids,
            from_date=month_start,
            to_date=date(month_end.year, month_end.month, 1),
        )
        return sum(
            float(t.amount)
            for t in transactions
            if t.category_id == budget.category_id and t.type == "expense"
        )

    def _enrich(self, budget, account_ids: list[uuid.UUID]) -> BudgetSchema:
        schema = BudgetSchema.model_validate(budget)
        spent = self._compute_spent(budget, account_ids)
        limit = float(budget.limit_amount)
        schema.spent = round(spent, 2)
        schema.remaining = round(max(limit - spent, 0), 2)
        schema.percent_used = round((spent / limit * 100) if limit > 0 else 0, 1)
        return schema

    def create(self, user_id: uuid.UUID, data: BudgetCreate) -> BudgetSchema:
        category = self._category_repo.get_by_name_and_type(data.category, "expense", user_id=user_id)
        if category is None:
            raise NotFoundError(f"Categoría de gasto '{data.category}' no encontrada")

        month_first = data.month.replace(day=1)
        existing = self._budget_repo.get_by_user_category_month(user_id, category.id, month_first)
        if existing:
            raise ValueError(f"Ya existe un presupuesto para '{data.category}' en {month_first.strftime('%Y-%m')}")

        budget = self._budget_repo.create(
            user_id=user_id,
            category_id=category.id,
            month=month_first,
            limit_amount=data.limit_amount,
            currency=data.currency,
        )
        account_ids = [a.id for a in self._account_repo.get_by_user(user_id)]
        return self._enrich(budget, account_ids)

    def get_by_user(self, user_id: uuid.UUID, month: date | None = None) -> list[BudgetSchema]:
        budgets = self._budget_repo.get_by_user(user_id, month=month)
        account_ids = [a.id for a in self._account_repo.get_by_user(user_id)]
        return [self._enrich(b, account_ids) for b in budgets]

    def update(self, budget_id: uuid.UUID, data: BudgetUpdate) -> BudgetSchema:
        budget = self._budget_repo.get_by_id(budget_id)
        if budget is None:
            raise NotFoundError(f"Budget {budget_id} not found")
        updated = self._budget_repo.update(budget_id, limit_amount=data.limit_amount, currency=data.currency)
        account_ids = [a.id for a in self._account_repo.get_by_user(updated.user_id)]
        return self._enrich(updated, account_ids)

    def delete(self, budget_id: uuid.UUID) -> None:
        if not self._budget_repo.delete(budget_id):
            raise NotFoundError(f"Budget {budget_id} not found")
