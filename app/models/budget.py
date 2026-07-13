"""Budget and BudgetAlert models."""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Budget(Base):
    """Monthly budget limit per category."""

    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False,
    )
    month: Mapped[date] = mapped_column(Date, nullable=False)  # primer día del mes: 2025-06-01
    limit_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.code"), nullable=False, default="PEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    category: Mapped["Category"] = relationship("Category")
    alerts: Mapped[list["BudgetAlert"]] = relationship(
        "BudgetAlert", back_populates="budget", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "month", name="uq_budget_user_category_month"),
    )


class BudgetAlert(Base):
    """Alert triggered when a budget reaches a threshold percentage."""

    __tablename__ = "budget_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False,
    )
    threshold_percent: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-100
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="alerts")

    __table_args__ = (
        CheckConstraint("threshold_percent BETWEEN 1 AND 100", name="ck_threshold_percent"),
    )
