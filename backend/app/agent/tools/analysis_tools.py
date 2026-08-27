import json
from datetime import date, timedelta
from langchain_core.tools import tool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.transaction import Transaction
from ...models.category import Category
from ...models.budget import Budget


@tool
async def analyze_spending(
    db: AsyncSession,
    user_id: int,
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
    db: AsyncSession,
    user_id: int,
) -> str:
    """检查本月预算使用情况，返回超支预警。"""
    try:
        today = date.today()
        year = today.year
        month = today.month
        start_date = today.replace(day=1)
        
        result = await db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.year == year,
                (Budget.month == month) | (Budget.month.is_(None))
            )
        )
        budgets = result.scalars().all()
        
        alerts = []
        budget_status = []
        
        for budget in budgets:
            query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= today,
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
