from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List


class TransactionCreate(BaseModel):
    account_id: int
    transfer_account_id: Optional[int] = None
    category_id: Optional[int] = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    transaction_type: str = Field(..., pattern="^(income|expense|transfer)$")
    description: Optional[str] = None
    transaction_date: date
    tags: Optional[List[str]] = None


class TransactionUpdate(BaseModel):
    account_id: Optional[int] = None
    transfer_account_id: Optional[int] = None
    category_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    transaction_type: Optional[str] = Field(None, pattern="^(income|expense|transfer)$")
    description: Optional[str] = None
    transaction_date: Optional[date] = None
    tags: Optional[List[str]] = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    transfer_account_id: Optional[int] = None
    category_id: int
    amount: Decimal
    transaction_type: str
    description: Optional[str]
    transaction_date: date
    tags: Optional[str]
    created_at: datetime
    # Joined fields
    account_name: Optional[str] = None
    transfer_account_name: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    transaction_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    keyword: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
