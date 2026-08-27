import json
from datetime import datetime, date
from decimal import Decimal
from langchain_core.tools import tool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.transaction import Transaction
from ...models.account import Account
from ...models.category import Category


@tool
async def add_transaction(
    db: AsyncSession,
    user_id: int,
    amount: float,
    transaction_type: str,
    description: str,
    account_name: str = "default",
    category_name: str = "other",
    transaction_date: str = None,
) -> str:
    """记录一笔收入或支出交易。
    
    Args:
        amount: 金额（正数）
        transaction_type: 交易类型，income(收入) 或 expense(支出)
        description: 交易描述
        account_name: 账户名称，默认为"default"
        category_name: 分类名称，默认为"other"
        transaction_date: 交易日期，格式YYYY-MM-DD，默认为今天
    """
    try:
        result = await db.execute(
            select(Account).where(Account.user_id == user_id, Account.name.ilike(f"%{account_name}%"))
        )
        account = result.scalar_one_or_none()
        if not account:
            account = Account(user_id=user_id, name="默认账户", account_type="cash", balance=0)
            db.add(account)
            await db.flush()
        
        result = await db.execute(
            select(Category).where(
                (Category.user_id == user_id) | (Category.is_system == True),
                Category.name.ilike(f"%{category_name}%"),
                Category.category_type == transaction_type
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            category_name_default = "其他收入" if transaction_type == "income" else "其他支出"
            result = await db.execute(
                select(Category).where(Category.name == category_name_default, Category.is_system == True)
            )
            category = result.scalar_one_or_none()
            if not category:
                category = Category(name=category_name_default, category_type=transaction_type, is_system=True)
                db.add(category)
                await db.flush()
        
        if transaction_date:
            txn_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
        else:
            txn_date = date.today()
        
        amount_decimal = Decimal(str(amount))
        transaction = Transaction(
            user_id=user_id,
            account_id=account.id,
            category_id=category.id,
            amount=amount_decimal,
            transaction_type=transaction_type,
            description=description,
            transaction_date=txn_date,
        )
        db.add(transaction)
        
        if transaction_type == "income":
            account.balance += amount_decimal
        else:
            account.balance -= amount_decimal
        
        await db.flush()
        
        type_str = "收入" if transaction_type == "income" else "支出"
        return json.dumps({
            "success": True,
            "message": f"已记录{type_str}：{description}，金额 ¥{amount:.2f}",
            "transaction_id": transaction.id,
            "account_balance": float(account.balance),
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
async def query_transactions(
    db: AsyncSession,
    user_id: int,
    start_date: str = None,
    end_date: str = None,
    transaction_type: str = None,
    category_name: str = None,
    limit: int = 20,
) -> str:
    """查询交易记录。
    
    Args:
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
        transaction_type: 交易类型过滤，income或expense
        category_name: 分类名称过滤
        limit: 返回数量限制
    """
    try:
        query = select(Transaction, Account.name, Category.name).join(
            Account, Transaction.account_id == Account.id
        ).join(
            Category, Transaction.category_id == Category.id
        ).where(Transaction.user_id == user_id)
        
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if category_name:
            query = query.where(Category.name.ilike(f"%{category_name}%"))
        
        query = query.order_by(Transaction.transaction_date.desc()).limit(limit)
        
        result = await db.execute(query)
        rows = result.all()
        
        transactions = []
        for txn, account_name, category_name in rows:
            transactions.append({
                "id": txn.id,
                "date": txn.transaction_date.isoformat(),
                "type": txn.transaction_type,
                "amount": float(txn.amount),
                "description": txn.description,
                "account": account_name,
                "category": category_name,
            })
        
        return json.dumps({
            "success": True,
            "count": len(transactions),
            "transactions": transactions,
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
