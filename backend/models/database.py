from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# ==================== 本地 SQLite (LLM 配置) ====================
local_engine = create_async_engine(
    settings.LOCAL_DB_URL,
    echo=False,  # 本地配置不需要输出 SQL
    future=True,
)

local_session_maker = async_sessionmaker(
    local_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class LocalBase(DeclarativeBase):
    """本地数据库的 Model 基类 (LLM 配置)"""
    pass


# ==================== 远程 PostgreSQL (业务数据) ====================
remote_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # 业务数据保持 SQL 输出便于调试
    future=True,
)

remote_session_maker = async_sessionmaker(
    remote_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class RemoteBase(DeclarativeBase):
    """远程数据库的 Model 基类 (业务数据)"""
    pass


# ==================== 兼容性别名 ====================
# 保持向后兼容，现有代码中的 Base 和 async_session_maker 默认指向远程数据库
Base = RemoteBase
async_session_maker = remote_session_maker
engine = remote_engine


# ==================== 数据库初始化 ====================
async def init_db():
    """Initialize both databases"""
    # 1. 初始化本地 SQLite (LLM 配置)
    async with local_engine.begin() as conn:
        await conn.run_sync(LocalBase.metadata.create_all)
    print("✅ Local database (SQLite) initialized for LLM configs")

    # 2. 初始化远程 PostgreSQL (业务数据)
    async with remote_engine.begin() as conn:
        await conn.run_sync(RemoteBase.metadata.create_all)
    print("✅ Remote database (PostgreSQL) initialized for business data")


# ==================== 依赖注入函数 ====================
async def get_local_db() -> AsyncSession:
    """Dependency for getting LOCAL database session (LLM configs)"""
    async with local_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """Dependency for getting REMOTE database session (business data)"""
    async with remote_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 别名，保持向后兼容
get_remote_db = get_db
