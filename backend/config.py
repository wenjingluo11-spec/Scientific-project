from pydantic_settings import BaseSettings
from functools import lru_cache


import os
# Force clear env var that might be lingering
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

class Settings(BaseSettings):
    # API Keys - 使用旧项目的 key
    ANTHROPIC_API_KEY: str = "sk-f3cdd22cdf5340c78eca9cc4f9b6258c"
    
    # Google Gemini API Key (用于 Deep Research)
    GOOGLE_API_KEY: str = "AIzaSyCGsb2h4liLLrU_zHE7YORNCyG9pAugXGg"

    # Anthropic API Configuration - 注意：SDK 会自动拼接 /v1/messages
    ANTHROPIC_BASE_URL: str = "http://127.0.0.1:8045"

    # Database - 远程 PostgreSQL (业务数据)
    DATABASE_URL: str = "postgresql+asyncpg://llm_dev:tphy%40123@182.92.74.187:9124/research"
    
    # Database - 本地 SQLite (LLM 配置)
    LOCAL_DB_URL: str = "sqlite+aiosqlite:///./database/local_config.db"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    # Agent Settings
    MAX_ITERATIONS: int = 3
    DEFAULT_MODEL: str = "claude-haiku-4-5"  # 与旧项目一致
    MAX_TOKENS: int = 20000  # 增加到 4096，与旧项目一致
    API_TIMEOUT: int = 120  # 与旧项目一致

    # Web Scraping
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
