from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional


class BudgetCreate(BaseModel):
    category_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    period: str = Field(default="monthly", pattern="^(weekly|monthly|yearly)$")
    year: int = Field(..., ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    alert_threshold: Decimal = Field(default=80, ge=0, le=100, decimal_places=2)


class BudgetResponse(BaseModel):
    id: int
    category_id: Optional[int]
    amount: Decimal
    period: str
    year: int
    month: Optional[int]
    alert_threshold: Decimal
    created_at: datetime
    # Computed fields
    spent: Optional[Decimal] = None
    remaining: Optional[Decimal] = None
    usage_percent: Optional[Decimal] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True
