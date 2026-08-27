from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.session import init_db
from .api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_default_categories()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API v{settings.APP_VERSION}"}


@app.get("/health")
async def health():
    return {"status": "ok"}


async def seed_default_categories():
    """初始化默认分类"""
    from sqlalchemy import select
    from .db.session import async_session
    from .models.category import Category
    
    default_categories = [
        ("餐饮", "expense"), ("交通", "expense"), ("购物", "expense"),
        ("娱乐", "expense"), ("住房", "expense"), ("医疗", "expense"),
        ("教育", "expense"), ("日用品", "expense"), ("通讯", "expense"),
        ("服饰", "expense"), ("其他支出", "expense"),
        ("工资", "income"), ("奖金", "income"), ("投资收益", "income"),
        ("兼职", "income"), ("红包", "income"), ("其他收入", "income"),
    ]
    
    async with async_session() as session:
        for name, cat_type in default_categories:
            result = await session.execute(
                select(Category).where(Category.name == name, Category.is_system == True)
            )
            if not result.scalar_one_or_none():
                session.add(Category(name=name, category_type=cat_type, is_system=True))
        await session.commit()
