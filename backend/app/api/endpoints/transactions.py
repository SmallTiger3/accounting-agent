import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ...api.deps import get_current_user
from ...db.session import get_db
from ...models.account import Account
from ...models.category import Category
from ...models.transaction import Transaction
from ...models.user import User
from ...schemas.transaction import TransactionCreate
from ...services.transaction_rules import get_balance_deltas, validate_transaction_type

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
    transfer_account = aliased(Account)
    query = select(
        Transaction,
        Account.name.label("account_name"),
        transfer_account.name.label("transfer_account_name"),
        Category.name.label("category_name"),
    ).join(
        Account, Transaction.account_id == Account.id
    ).outerjoin(
        transfer_account, Transaction.transfer_account_id == transfer_account.id
    ).join(
        Category, Transaction.category_id == Category.id
    ).where(Transaction.user_id == current_user.id)

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if transaction_type:
        try:
            validate_transaction_type(transaction_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        query = query.where(Transaction.transaction_type == transaction_type)
    if start_date:
        query = query.where(Transaction.transaction_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.where(Transaction.transaction_date <= date.fromisoformat(end_date))
    if keyword:
        query = query.where(Transaction.description.ilike(f"%{keyword}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    result = await db.execute(
        query.order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    items = []
    for txn, account_name, transfer_account_name, category_name in result.all():
        items.append({
            "id": txn.id,
            "account_id": txn.account_id,
            "transfer_account_id": txn.transfer_account_id,
            "category_id": txn.category_id,
            "amount": float(txn.amount),
            "transaction_type": txn.transaction_type,
            "description": txn.description,
            "transaction_date": txn.transaction_date.isoformat(),
            "tags": txn.tags,
            "created_at": txn.created_at.isoformat(),
            "account_name": account_name,
            "transfer_account_name": transfer_account_name,
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
    try:
        validate_transaction_type(txn_data.transaction_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await db.execute(select(Account).where(
        Account.id == txn_data.account_id,
        Account.user_id == current_user.id,
    ))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transfer_account = None
    if txn_data.transaction_type == "transfer":
        if not txn_data.transfer_account_id or txn_data.transfer_account_id == txn_data.account_id:
            raise HTTPException(status_code=400, detail="A transfer requires two different accounts")
        result = await db.execute(select(Account).where(
            Account.id == txn_data.transfer_account_id,
            Account.user_id == current_user.id,
        ))
        transfer_account = result.scalar_one_or_none()
        if not transfer_account:
            raise HTTPException(status_code=404, detail="Transfer destination account not found")
    elif txn_data.category_id is None:
        raise HTTPException(status_code=400, detail="Category is required for income and expense")

    txn_dict = txn_data.model_dump()
    txn_dict["user_id"] = current_user.id
    if txn_data.transaction_type != "transfer":
        txn_dict["transfer_account_id"] = None
    if txn_data.transaction_type == "transfer":
        result = await db.execute(select(Category).where(
            Category.category_type == "transfer",
            Category.is_system.is_(True),
        ))
        category = result.scalar_one_or_none()
        if not category:
            category = Category(name="转账", category_type="transfer", is_system=True)
            db.add(category)
            await db.flush()
        txn_dict["category_id"] = category.id
    if txn_dict.get("tags"):
        txn_dict["tags"] = json.dumps(txn_dict["tags"])

    transaction = Transaction(**txn_dict)
    db.add(transaction)

    source_delta, _ = get_balance_deltas(txn_data.amount, txn_data.transaction_type)
    account.balance += source_delta
    if transfer_account:
        _, destination_delta = get_balance_deltas(
            txn_data.amount, txn_data.transaction_type, is_source=False
        )
        transfer_account.balance += destination_delta

    await db.flush()
    await db.refresh(transaction)
    return {
        "id": transaction.id,
        "amount": float(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "account_balance": float(account.balance),
        "transfer_account_balance": float(transfer_account.balance) if transfer_account else None,
    }


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Transaction).where(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
    ))
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    result = await db.execute(select(Account).where(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id,
    ))
    account = result.scalar_one()
    if transaction.transaction_type == "income":
        account.balance -= transaction.amount
    elif transaction.transaction_type == "expense":
        account.balance += transaction.amount
    elif transaction.transaction_type == "transfer":
        account.balance += transaction.amount
        if transaction.transfer_account_id:
            result = await db.execute(select(Account).where(
                Account.id == transaction.transfer_account_id,
                Account.user_id == current_user.id,
            ))
            transfer_account = result.scalar_one_or_none()
            if transfer_account:
                transfer_account.balance -= transaction.amount

    await db.delete(transaction)
    await db.flush()
