from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date
import json

from ...db.session import get_db
from ...models.transaction import Transaction
from ...models.account import Account
from ...models.category import Category
from ...schemas.transaction import TransactionCreate
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/transactions", tags=["交易"])


@router.get("/", response_model=dict)
async def list_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取交易列表"""
    query = select(
        Transaction, Account.name.label("account_name"), Category.name.label("category_name")
    ).join(Account, Transaction.account_id == Account.id
    ).join(Category, Transaction.category_id == Category.id
    ).where(Transaction.user_id == current_user.id)
    
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    if start:
        query = query.where(Transaction.transaction_date >= start)
    if end:
        query = query.where(Transaction.transaction_date <= end)
    if keyword:
        query = query.where(Transaction.description.ilike(f"%{keyword}%"))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    
    query = query.order_by(Transaction.transaction_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for txn, account_name, category_name in rows:
        items.append({
            "id": txn.id,
            "account_id": txn.account_id,
            "category_id": txn.category_id,
            "amount": float(txn.amount),
            "transaction_type": txn.transaction_type,
            "description": txn.description,
            "transaction_date": txn.transaction_date.isoformat(),
            "tags": txn.tags,
            "created_at": txn.created_at.isoformat(),
            "account_name": account_name,
            "category_name": category_name,
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/", status_code=201)
async def create_transaction(
    txn_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建交易"""
    result = await db.execute(
        select(Account).where(Account.id == txn_data.account_id, Account.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    txn_dict = txn_data.model_dump()
    txn_dict["user_id"] = current_user.id
    if txn_dict.get("tags"):
        txn_dict["tags"] = json.dumps(txn_dict["tags"])
    
    transaction = Transaction(**txn_dict)
    db.add(transaction)
    
    if txn_data.transaction_type == "income":
        account.balance += txn_data.amount
    else:
        account.balance -= txn_data.amount
    
    await db.flush()
    await db.refresh(transaction)
    
    return {
        "id": transaction.id,
        "amount": float(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "account_balance": float(account.balance),
    }


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除交易"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    result = await db.execute(select(Account).where(Account.id == transaction.account_id))
    account = result.scalar_one()
    if transaction.transaction_type == "income":
        account.balance -= transaction.amount
    else:
        account.balance += transaction.amount
    
    await db.delete(transaction)
    await db.flush()
