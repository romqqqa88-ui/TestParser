from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/avito_parser"

    request_timeout: int = 20
    request_retries: int = 3
    request_delay_seconds: float = 1.0
    max_pages_per_query: int = 5
    max_concurrency: int = 5
    user_agent: str = "Mozilla/5.0"

    proxy_enabled: bool = False
    proxy_list: str = ""

    export_dir: str = "exports"
    export_max_rows_per_file: int = 50000

    scheduler_enabled: bool = False
    scheduler_timezone: str = "Europe/Moscow"
    scheduler_interval_minutes: int = Field(default=60, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
