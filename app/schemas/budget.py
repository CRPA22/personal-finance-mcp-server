"""Budget schemas."""

import uuid
from datetime import date as date_cls, datetime

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)  # nombre de categoría
    month: date_cls                                            # primer día del mes
    limit_amount: float = Field(..., gt=0)
    currency: str = Field(default="PEN", min_length=3, max_length=3)


class BudgetUpdate(BaseModel):
    limit_amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class BudgetSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    category: str = ""
    month: date_cls
    limit_amount: float
    currency: str
    spent: float = 0.0          # calculado en el servicio
    remaining: float = 0.0
    percent_used: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "category") and hasattr(obj.category, "name"):
            instance.category = obj.category.name
        return instance
