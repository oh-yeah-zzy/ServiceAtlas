"""
数据库连接与初始化模块
使用 SQLAlchemy 2.0 异步模式 + aiosqlite
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # debug 模式下打印 SQL
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 的 Depends
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
