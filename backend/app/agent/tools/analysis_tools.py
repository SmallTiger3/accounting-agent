import json
from contextvars import ContextVar
from datetime import date, timedelta
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.transaction import Transaction
from ...models.category import Category
from ...models.budget import Budget
from ...services.budget_periods import get_period_bounds, clamp_period_to_today

_db_var: ContextVar[Optional[AsyncSession]] = ContextVar("analysis_db", default=None)
_user_id_var: ContextVar[Optional[int]] = ContextVar("analysis_user_id", default=None)


def set_db_session(db: AsyncSession, user_id: int) -> None:
    """设置当前请求的数据库会话和用户ID（供Agent工具使用）。"""
    _db_var.set(db)
    _user_id_var.set(user_id)


def _get_db() -> AsyncSession:
    db = _db_var.get()
    if db is None:
        raise RuntimeError("数据库会话未初始化，请先调用 set_db_session")
    return db


def _get_user_id() -> int:
    user_id = _user_id_var.get()
    if user_id is None:
        raise RuntimeError("用户未初始化，请先调用 set_db_session")
    return user_id


@tool
async def analyze_spending(
    period: str = "month",
    start_date: str = None,
    end_date: str = None,
) -> str:
    """分析消费情况，按分类统计。
    
    Args:
        period: 时间范围，today/week/month/year/custom
        start_date: 自定义开始日期（period=custom时使用）
        end_date: 自定义结束日期（period=custom时使用）
    """
    try:
        db = _get_db()
        user_id = _get_user_id()

        today = date.today()
        
        if period == "today":
            start = end = today
        elif period == "week":
            start = today - timedelta(days=today.weekday())
            end = today
        elif period == "month":
            start = today.replace(day=1)
            end = today
        elif period == "year":
            start = today.replace(month=1, day=1)
            end = today
        elif period == "custom" and start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        else:
            start = today.replace(day=1)
            end = today
        
        result = await db.execute(
            select(
                Category.name,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count")
            ).join(Category, Transaction.category_id == Category.id).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc())
        )
        expense_by_category = result.all()
        
        result = await db.execute(
            select(
                Category.name,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count")
            ).join(Category, Transaction.category_id == Category.id).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "income",
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc())
        )
        income_by_category = result.all()
        
        total_expense = sum(float(row.total) for row in expense_by_category)
        total_income = sum(float(row.total) for row in income_by_category)
        
        return json.dumps({
            "success": True,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_income": total_income - total_expense,
            },
            "expense_by_category": [
                {"category": row.name, "amount": float(row.total), "count": row.count}
                for row in expense_by_category
            ],
            "income_by_category": [
                {"category": row.name, "amount": float(row.total), "count": row.count}
                for row in income_by_category
            ],
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@tool
async def check_budget(
) -> str:
    """检查本月预算使用情况，返回超支预警。"""
    try:
        db = _get_db()
        user_id = _get_user_id()

        today = date.today()
        year = today.year
        month = today.month
        result = await db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.year == year,
                ((Budget.period == "yearly") |
                 ((Budget.period.in_(["monthly", "weekly"])) &
                  ((Budget.month == month) | (Budget.month.is_(None)))))
            )
        )
        budgets = result.scalars().all()
        
        alerts = []
        budget_status = []
        
        for budget in budgets:
            start_date, end_date = get_period_bounds(budget.period, year, budget.month or month, today)
            start_date, end_date = clamp_period_to_today(start_date, end_date, today)
            query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            
            if budget.category_id:
                query = query.where(Transaction.category_id == budget.category_id)
                cat_result = await db.execute(select(Category.name).where(Category.id == budget.category_id))
                category_name = cat_result.scalar_one_or_none() or "未知"
            else:
                category_name = "总预算"
            
            spent_result = await db.execute(query)
            spent = float(spent_result.scalar_one())
            budget_amount = float(budget.amount)
            usage_percent = (spent / budget_amount * 100) if budget_amount > 0 else 0
            
            status = {
                "category": category_name,
                "budget": budget_amount,
                "spent": spent,
                "remaining": budget_amount - spent,
                "usage_percent": round(usage_percent, 1),
            }
            budget_status.append(status)
            
            if usage_percent >= 100:
                alerts.append(f"⚠️ {category_name}预算已超支！预算 ¥{budget_amount:.2f}，已花费 ¥{spent:.2f}")
            elif usage_percent >= float(budget.alert_threshold):
                alerts.append(f"⚡ {category_name}预算即将用尽（{usage_percent:.1f}%），剩余 ¥{budget_amount - spent:.2f}")
        
        return json.dumps({
            "success": True,
            "budget_status": budget_status,
            "alerts": alerts,
            "has_alerts": len(alerts) > 0,
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
