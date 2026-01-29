from pydantic_settings import BaseSettings
from functools import lru_cache


import os
# Force clear env var that might be lingering
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

class Settings(BaseSettings):
    # API Keys - 使用旧项目的 key
    ANTHROPIC_API_KEY: str = "sk-691331534d4a403fbd2add1841357a8f"

    # Anthropic API Configuration - 注意：SDK 会自动拼接 /v1/messages
    ANTHROPIC_BASE_URL: str = "http://127.0.0.1:8045"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./database/scientific.db"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    # Agent Settings
    MAX_ITERATIONS: int = 3
    DEFAULT_MODEL: str = "claude-haiku-4-5"  # 与旧项目一致
    MAX_TOKENS: int = 4096  # 增加到 4096，与旧项目一致
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
