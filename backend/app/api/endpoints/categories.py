from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...db.session import get_db
from ...models.category import Category
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("/")
async def list_categories(
    category_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取分类列表"""
    query = select(Category).where(
        (Category.user_id == current_user.id) | (Category.is_system == True)
    )
    if category_type:
        query = query.where(Category.category_type == category_type)
    
    query = query.order_by(Category.is_system.desc(), Category.name)
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "category_type": c.category_type,
            "icon": c.icon,
            "is_system": c.is_system,
        }
        for c in categories
    ]
