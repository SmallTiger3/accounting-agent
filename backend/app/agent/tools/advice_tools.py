import json
from datetime import date, timedelta
from langchain_core.tools import tool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.transaction import Transaction
from ...models.category import Category


@tool
async def get_spending_insights(
    db: AsyncSession,
    user_id: int,
    months: int = 3,
) -> str:
    """获取消费洞察和趋势数据，用于生成财务建议。
    
    Args:
        months: 分析最近几个月的数据
    """
    try:
        today = date.today()
        insights = []
        
        for i in range(months):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            year = month_date.year
            month = month_date.month
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            
            result = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == "expense",
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end,
                )
            )
            total_expense = float(result.scalar_one())
            
            result = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == "income",
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end,
                )
            )
            total_income = float(result.scalar_one())
            
            result = await db.execute(
                select(Category.name, func.sum(Transaction.amount).label("total")).join(
                    Category, Transaction.category_id == Category.id
                ).where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_type == "expense",
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end,
                ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).limit(3)
            )
            top_categories = [{"category": row.name, "amount": float(row.total)} for row in result.all()]
            
            insights.append({
                "month": f"{year}-{month:02d}",
                "total_income": total_income,
                "total_expense": total_expense,
                "savings": total_income - total_expense,
                "savings_rate": ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0,
                "top_expense_categories": top_categories,
            })
        
        if len(insights) >= 2:
            recent = insights[0]["total_expense"]
            previous = insights[1]["total_expense"]
            trend = "上升" if recent > previous else "下降" if recent < previous else "持平"
            change_percent = ((recent - previous) / previous * 100) if previous > 0 else 0
        else:
            trend = "数据不足"
            change_percent = 0
        
        return json.dumps({
            "success": True,
            "monthly_insights": insights,
            "trend": {
                "direction": trend,
                "change_percent": round(change_percent, 1),
            },
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
