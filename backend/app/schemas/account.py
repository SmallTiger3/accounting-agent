from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(default="cash", pattern="^(cash|bank|credit|investment)$")
    balance: Decimal = Field(default=0, decimal_places=2)
    currency: str = Field(default="CNY", max_length=3)
    description: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    account_type: Optional[str] = Field(None, pattern="^(cash|bank|credit|investment)$")
    description: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: str
    balance: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
