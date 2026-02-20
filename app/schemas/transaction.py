"""Transaction schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Input for creating a transaction."""

    account_id: uuid.UUID
    amount: float = Field(..., gt=0)
    type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=100)
    date: date
    description: str | None = Field(default=None, max_length=500)


class TransactionSchema(BaseModel):
    """Transaction output schema."""

    id: uuid.UUID
    account_id: uuid.UUID
    amount: float
    type: str
    category: str
    date: date
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
