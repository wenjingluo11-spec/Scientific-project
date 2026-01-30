"""LLM Configuration Model - 存储多个 LLM 配置"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from models.database import Base
from datetime import datetime


class LLMConfig(Base):
    """LLM 模型配置"""
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    provider = Column(String(50), default="anthropic")  # anthropic/openai/deepseek/custom
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)  # 直接存储
    default_model = Column(String(100), nullable=False)
    max_tokens = Column(Integer, default=4096)
    timeout = Column(Integer, default=120)
    is_primary = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "default_model": self.default_model,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_config_dict(self) -> dict:
        """转换为 AnthropicClient 可用的配置字典"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

