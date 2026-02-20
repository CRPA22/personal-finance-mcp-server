"""Account schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    """Input for creating an account."""

    user_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(checking|savings|investment)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    initial_balance: float = Field(default=0, ge=-1e12, le=1e12)


class AccountSchema(BaseModel):
    """Account output schema."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    currency: str
    balance: float
    created_at: datetime

    model_config = {"from_attributes": True}
