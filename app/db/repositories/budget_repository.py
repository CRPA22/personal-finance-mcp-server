"""Budget repository."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget, BudgetAlert


class BudgetRepository:
    """Repository for Budget CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        month: date,
        limit_amount: float,
        currency: str = "PEN",
    ) -> Budget:
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            month=month,
            limit_amount=limit_amount,
            currency=currency,
        )
        self._session.add(budget)
        self._session.flush()
        return budget

    def get_by_id(self, budget_id: uuid.UUID) -> Budget | None:
        return self._session.scalars(select(Budget).where(Budget.id == budget_id)).first()

    def get_by_user(self, user_id: uuid.UUID, month: date | None = None) -> list[Budget]:
        stmt = select(Budget).where(Budget.user_id == user_id)
        if month:
            stmt = stmt.where(Budget.month == month)
        stmt = stmt.order_by(Budget.month.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_user_category_month(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        month: date,
    ) -> Budget | None:
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
        )
        return self._session.scalars(stmt).first()

    def update(
        self,
        budget_id: uuid.UUID,
        limit_amount: float | None = None,
        currency: str | None = None,
    ) -> Budget | None:
        budget = self.get_by_id(budget_id)
        if budget is None:
            return None
        if limit_amount is not None:
            budget.limit_amount = limit_amount
        if currency is not None:
            budget.currency = currency
        self._session.flush()
        return budget

    def delete(self, budget_id: uuid.UUID) -> bool:
        budget = self.get_by_id(budget_id)
        if budget is None:
            return False
        self._session.delete(budget)
        self._session.flush()
        return True

    def add_alert(self, budget_id: uuid.UUID, threshold_percent: int) -> BudgetAlert:
        alert = BudgetAlert(budget_id=budget_id, threshold_percent=threshold_percent)
        self._session.add(alert)
        self._session.flush()
        return alert
