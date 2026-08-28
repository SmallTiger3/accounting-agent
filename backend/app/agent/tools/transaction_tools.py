import json
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.account import Account
from ...models.category import Category
from ...models.transaction import Transaction
from ...services.transaction_rules import get_balance_deltas, validate_transaction_type

_db_var: ContextVar[Optional[AsyncSession]] = ContextVar("txn_db", default=None)
_user_id_var: ContextVar[Optional[int]] = ContextVar("txn_user_id", default=None)


def set_db_session(db: AsyncSession, user_id: int) -> None:
    _db_var.set(db)
    _user_id_var.set(user_id)


def _get_db() -> AsyncSession:
    db = _db_var.get()
    if db is None:
        raise RuntimeError("Database session is not initialized")
    return db


def _get_user_id() -> int:
    user_id = _user_id_var.get()
    if user_id is None:
        raise RuntimeError("User is not initialized")
    return user_id


async def _get_or_create_system_transfer_category(db: AsyncSession) -> Category:
    result = await db.execute(select(Category).where(
        Category.category_type == "transfer",
        Category.is_system.is_(True),
    ))
    category = result.scalar_one_or_none()
    if category:
        return category

    category = Category(name="转账", category_type="transfer", is_system=True)
    db.add(category)
    await db.flush()
    return category


@tool
async def add_transaction(
    amount: float,
    transaction_type: str,
    description: str,
    account_name: str = "default",
    category_name: str = "other",
    transaction_date: str = None,
    transfer_account_name: str = None,
) -> str:
    """Record an income, expense, or transfer transaction.

    For transfers, account_name is the source account and
    transfer_account_name is the destination account.
    """
    try:
        validate_transaction_type(transaction_type)
        db = _get_db()
        user_id = _get_user_id()
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return json.dumps({"success": False, "error": "Amount must be greater than zero"})

        result = await db.execute(select(Account).where(
            Account.user_id == user_id,
            Account.name.ilike(f"%{account_name}%"),
        ))
        account = result.scalar_one_or_none()
        if not account:
            account = Account(user_id=user_id, name="默认账户", account_type="cash", balance=0)
            db.add(account)
            await db.flush()

        transfer_account = None
        if transaction_type == "transfer":
            if not transfer_account_name:
                return json.dumps({"success": False, "error": "Transfer destination is required"})
            result = await db.execute(select(Account).where(
                Account.user_id == user_id,
                Account.name.ilike(f"%{transfer_account_name}%"),
            ))
            transfer_account = result.scalar_one_or_none()
            if not transfer_account or transfer_account.id == account.id:
                return json.dumps({"success": False, "error": "Transfer destination is invalid"})

        if transaction_type == "transfer":
            category = await _get_or_create_system_transfer_category(db)
        else:
            result = await db.execute(select(Category).where(
                (Category.user_id == user_id) | (Category.is_system.is_(True)),
                Category.name.ilike(f"%{category_name}%"),
                Category.category_type == transaction_type,
            ))
            category = result.scalar_one_or_none()
            fallback_name = "其他收入" if transaction_type == "income" else "其他支出"
            if not category:
                result = await db.execute(select(Category).where(
                    Category.name == fallback_name,
                    Category.is_system.is_(True),
                ))
                category = result.scalar_one_or_none()
            if not category:
                category = Category(
                    name=fallback_name,
                    category_type=transaction_type,
                    is_system=True,
                )
                db.add(category)
                await db.flush()

        txn_date = (
            datetime.strptime(transaction_date, "%Y-%m-%d").date()
            if transaction_date else date.today()
        )
        transaction = Transaction(
            user_id=user_id,
            account_id=account.id,
            transfer_account_id=transfer_account.id if transfer_account else None,
            category_id=category.id,
            amount=amount_decimal,
            transaction_type=transaction_type,
            description=description,
            transaction_date=txn_date,
        )
        db.add(transaction)

        source_delta, _ = get_balance_deltas(amount_decimal, transaction_type)
        account.balance += source_delta
        if transfer_account:
            _, destination_delta = get_balance_deltas(
                amount_decimal, transaction_type, is_source=False
            )
            transfer_account.balance += destination_delta

        await db.flush()
        type_name = {"income": "收入", "expense": "支出", "transfer": "转账"}[transaction_type]
        return json.dumps({
            "success": True,
            "message": f"已记录{type_name}：{description}，金额 ¥{amount:.2f}",
            "transaction_id": transaction.id,
            "account_balance": float(account.balance),
            "transfer_account_balance": (
                float(transfer_account.balance) if transfer_account else None
            ),
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


@tool
async def query_transactions(
    start_date: str = None,
    end_date: str = None,
    transaction_type: str = None,
    category_name: str = None,
    limit: int = 20,
) -> str:
    """Query transaction records."""
    try:
        if transaction_type:
            validate_transaction_type(transaction_type)
        db = _get_db()
        user_id = _get_user_id()
        query = select(Transaction, Account.name, Category.name).join(
            Account, Transaction.account_id == Account.id
        ).join(
            Category, Transaction.category_id == Category.id
        ).where(Transaction.user_id == user_id)

        if start_date:
            query = query.where(Transaction.transaction_date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(Transaction.transaction_date <= date.fromisoformat(end_date))
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if category_name:
            query = query.where(Category.name.ilike(f"%{category_name}%"))

        result = await db.execute(
            query.order_by(Transaction.transaction_date.desc()).limit(limit)
        )
        transactions = [
            {
                "id": txn.id,
                "date": txn.transaction_date.isoformat(),
                "type": txn.transaction_type,
                "amount": float(txn.amount),
                "description": txn.description,
                "account": account_name,
                "category": category_name,
            }
            for txn, account_name, category_name in result.all()
        ]
        return json.dumps({
            "success": True,
            "count": len(transactions),
            "transactions": transactions,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)
