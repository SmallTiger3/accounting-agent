from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import date

from ...db.session import get_db
from ...models.budget import Budget
from ...models.transaction import Transaction
from ...models.category import Category
from ...schemas.budget import BudgetCreate
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/budgets", tags=["预算"])


@router.get("/", response_model=List[dict])
async def list_budgets(
    year: int = None,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预算列表"""
    today = date.today()
    year = year or today.year
    month = month or today.month
    
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.year == year,
            (Budget.month == month) | (Budget.month.is_(None)),
        )
    )
    budgets = result.scalars().all()
    
    budget_list = []
    start_date = date(year, month, 1)
    
    for budget in budgets:
        query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= today,
        )
        if budget.category_id:
            query = query.where(Transaction.category_id == budget.category_id)
        
        spent = float((await db.execute(query)).scalar_one())
        budget_amount = float(budget.amount)
        
        category_name = None
        if budget.category_id:
            cat_result = await db.execute(select(Category.name).where(Category.id == budget.category_id))
            category_name = cat_result.scalar_one_or_none()
        
        budget_list.append({
            "id": budget.id,
            "category_id": budget.category_id,
            "amount": budget_amount,
            "period": budget.period,
            "year": budget.year,
            "month": budget.month,
            "alert_threshold": float(budget.alert_threshold),
            "created_at": budget.created_at.isoformat(),
            "spent": spent,
            "remaining": budget_amount - spent,
            "usage_percent": round(spent / budget_amount * 100, 1) if budget_amount > 0 else 0,
            "category_name": category_name,
        })
    
    return budget_list


@router.post("/", status_code=201)
async def create_budget(
    budget_data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建预算"""
    budget = Budget(user_id=current_user.id, **budget_data.model_dump())
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    
    return {
        "id": budget.id,
        "amount": float(budget.amount),
        "period": budget.period,
        "year": budget.year,
        "month": budget.month,
    }


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除预算"""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    await db.delete(budget)
    await db.flush()
