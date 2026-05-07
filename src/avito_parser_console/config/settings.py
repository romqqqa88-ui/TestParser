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
    request_timeout_min_seconds: float = 1.0
    request_timeout_backoff_multiplier: float = 1.0
    request_timeout_max_seconds: float = 20.0
    request_retries: int = 6
    request_delay_seconds: float = 2.0
    request_min_retry_delay_seconds: float = 0.2
    request_backoff_multiplier: float = 2.0
    request_jitter_seconds: float = 0.3
    request_apply_jitter_to_retry_after: bool = False
    request_max_backoff_seconds: float = 90.0
    request_retry_after_max_seconds: float = 120.0
    request_retry_statuses: str = "429,403,503"
    request_retry_on_statuses: bool = True
    request_retry_on_exceptions: bool = True
    http_backend: str = "httpx"  # httpx | curl_cffi | auto
    http_backend_auto_order: str = "curl_cffi,httpx"
    curl_impersonate: str = "chrome124"
    max_pages_per_query: int = 5
    max_concurrency: int = 5
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    user_agent_pool: str = ""
    browser_headers_enabled: bool = True
    # Optional raw Cookie header value copied from a real browser (helps some 429-heavy IPs).
    request_cookie: str = ""

    proxy_enabled: bool = False
    proxy_list: str = ""
    proxy_rotate_on_retry: bool = True

    export_dir: str = "exports"
    export_max_rows_per_file: int = 50000

    scheduler_enabled: bool = False
    scheduler_timezone: str = "Europe/Moscow"
    scheduler_interval_minutes: int = Field(default=60, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
