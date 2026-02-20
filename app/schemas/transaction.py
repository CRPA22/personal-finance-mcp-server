"""Transaction schemas."""

import uuid
from datetime import date as date_cls, datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Input for creating a transaction."""

    account_id: uuid.UUID
    amount: float = Field(..., gt=0)
    type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=100)
    date: date_cls
    description: str | None = Field(default=None, max_length=500)


class TransactionUpdate(BaseModel):
    """Input for updating a transaction (all fields optional)."""

    amount: float | None = Field(default=None, gt=0)
    type: str | None = Field(default=None, pattern="^(income|expense)$")
    category: str | None = Field(default=None, min_length=1, max_length=100)
    date: date_cls | None = None
    description: str | None = Field(default=None, max_length=500)


class TransactionSchema(BaseModel):
    """Transaction output schema."""

    id: uuid.UUID
    account_id: uuid.UUID
    amount: float
    type: str
    category: str
    date: date_cls
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
