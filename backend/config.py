from pydantic_settings import BaseSettings
from functools import lru_cache


import os
# Force clear env var that might be lingering
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

class Settings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: str = "e934ab82-67ea-41f8-9d8d-b1aff85e7f74"

    # Anthropic API Configuration (Volcengine Compatible)
    ANTHROPIC_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./database/scientific.db"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    # Agent Settings
    MAX_ITERATIONS: int = 3
    DEFAULT_MODEL: str = "ep-20250416114912-nsdxw"  # Volcengine Endpoint ID
    MAX_TOKENS: int = 4000

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
