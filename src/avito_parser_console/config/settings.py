from functools import lru_cache
from pathlib import Path
import sys
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["dev", "prod"] = "dev"
    runtime_profile: Literal["default", "quasi_realtime"] = "default"
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
    # Comma-separated curl_cffi impersonate tokens; random choice per request (TLS fingerprint rotation).
    curl_impersonate_pool: str = "chrome124,chrome123,chrome120"
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
    # Optional path to a UTF-8 file whose contents are pasted Cookie header (refreshed without editing .env).
    request_cookie_file: str = ""

    proxy_enabled: bool = False
    proxy_list: str = ""
    proxy_rotate_on_retry: bool = True

    export_dir: str = "exports"
    export_max_rows_per_file: int = 50000
    new_listings_file: str = ""
    db_retries: int = 2
    db_retry_delay_seconds: float = 0.5
    db_retry_backoff_multiplier: float = 2.0
    db_retry_jitter_seconds: float = 0.2

    scheduler_enabled: bool = False
    scheduler_timezone: str = "Europe/Moscow"
    scheduler_interval_minutes: int = Field(default=60, ge=1)

    def model_post_init(self, __context: object) -> None:
        if self.runtime_profile != "quasi_realtime":
            return
        # Safer defaults for Avito polling loops: less bursty traffic, lower ban probability.
        self.request_retries = 2
        self.request_delay_seconds = 3.0
        self.request_min_retry_delay_seconds = 0.8
        self.request_backoff_multiplier = 2.5
        self.request_jitter_seconds = 1.2
        self.request_max_backoff_seconds = 180.0
        self.request_retry_after_max_seconds = 240.0
        self.max_concurrency = 1
        self.max_pages_per_query = 2
        self.scheduler_interval_minutes = 1


@lru_cache
def get_settings() -> Settings:
    env_candidates: list[Path] = []
    cwd = Path.cwd()
    env_candidates.append(cwd / ".env")
    env_candidates.append(cwd.parent / ".env")

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        env_candidates.append(exe_dir / ".env")
        env_candidates.append(exe_dir.parent / ".env")

    for env_path in env_candidates:
        if env_path.exists():
            return Settings(_env_file=env_path)

    return Settings()
