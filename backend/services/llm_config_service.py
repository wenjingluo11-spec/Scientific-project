"""LLM 配置服务 - 统一管理配置缓存"""

from typing import Optional
from models.llm_config import LLMConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


# 模块级缓存 - 存储主配置
_primary_config_cache: Optional[LLMConfig] = None


def get_cached_primary_config() -> Optional[LLMConfig]:
    """获取缓存的主配置（同步方法，供 AnthropicClient 使用）"""
    return _primary_config_cache


def set_cached_primary_config(config: Optional[LLMConfig]):
    """设置缓存"""
    global _primary_config_cache
    _primary_config_cache = config


def invalidate_config_cache():
    """清除缓存"""
    global _primary_config_cache
    _primary_config_cache = None


async def refresh_primary_config_cache(db: AsyncSession) -> Optional[LLMConfig]:
    """从数据库刷新主配置缓存"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_primary == True)
    )
    config = result.scalar_one_or_none()
    set_cached_primary_config(config)
    return config


async def get_all_configs(db: AsyncSession) -> list[LLMConfig]:
    """获取所有配置"""
    result = await db.execute(
        select(LLMConfig).order_by(LLMConfig.created_at.desc())
    )
    return list(result.scalars().all())


async def get_config_by_id(db: AsyncSession, config_id: int) -> Optional[LLMConfig]:
    """根据 ID 获取配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id)
    )
    return result.scalar_one_or_none()


async def create_config(db: AsyncSession, config_data: dict) -> LLMConfig:
    """创建新配置"""
    config = LLMConfig(
        name=config_data["name"],
        provider=config_data.get("provider", "anthropic"),
        base_url=config_data["base_url"],
        api_key=config_data["api_key"],
        default_model=config_data["default_model"],
        max_tokens=config_data.get("max_tokens", 4096),
        timeout=config_data.get("timeout", 120),
        is_primary=config_data.get("is_primary", False),
    )
    
    # 如果是第一个配置，自动设为主配置
    existing = await get_all_configs(db)
    if not existing:
        config.is_primary = True
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    # 如果设为主配置，更新缓存
    if config.is_primary:
        set_cached_primary_config(config)
    
    return config


async def update_config(db: AsyncSession, config_id: int, config_data: dict) -> Optional[LLMConfig]:
    """更新配置"""
    config = await get_config_by_id(db, config_id)
    if not config:
        return None
    
    # 更新字段
    if "name" in config_data:
        config.name = config_data["name"]
    if "provider" in config_data:
        config.provider = config_data["provider"]
    if "base_url" in config_data:
        config.base_url = config_data["base_url"]
    if "api_key" in config_data:
        config.api_key = config_data["api_key"]
    if "default_model" in config_data:
        config.default_model = config_data["default_model"]
    if "max_tokens" in config_data:
        config.max_tokens = config_data["max_tokens"]
    if "timeout" in config_data:
        config.timeout = config_data["timeout"]
    
    await db.commit()
    await db.refresh(config)
    
    # 如果是主配置，更新缓存
    if config.is_primary:
        set_cached_primary_config(config)
    
    return config


async def delete_config(db: AsyncSession, config_id: int) -> bool:
    """删除配置"""
    config = await get_config_by_id(db, config_id)
    if not config:
        return False
    
    was_primary = config.is_primary
    
    await db.delete(config)
    await db.commit()
    
    # 如果删除的是主配置，尝试切换到下一个
    if was_primary:
        remaining = await get_all_configs(db)
        if remaining:
            # 设置第一个为主配置
            remaining[0].is_primary = True
            await db.commit()
            set_cached_primary_config(remaining[0])
        else:
            # 没有配置了，清除缓存
            invalidate_config_cache()
    
    return True


async def set_primary_config(db: AsyncSession, config_id: int) -> Optional[LLMConfig]:
    """设置主配置（事务性操作）"""
    # 确保目标配置存在
    config = await get_config_by_id(db, config_id)
    if not config:
        return None
    
    # 清除所有主配置标记
    await db.execute(
        update(LLMConfig).values(is_primary=False)
    )
    
    # 设置新的主配置
    config.is_primary = True
    await db.commit()
    await db.refresh(config)
    
    # 更新缓存
    set_cached_primary_config(config)
    
    return config


async def get_primary_config(db: AsyncSession) -> Optional[LLMConfig]:
    """获取主配置（从缓存或数据库）"""
    cached = get_cached_primary_config()
    if cached:
        return cached
    
    # 缓存未命中，从数据库加载
    return await refresh_primary_config_cache(db)
