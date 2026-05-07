from __future__ import annotations

import asyncio
import random

import httpx

from avito_parser_console.config.settings import Settings
from avito_parser_console.parser.proxy_pool import ProxyPool


class AsyncHttpClient:
    def __init__(self, settings: Settings, proxy_pool: ProxyPool | None = None):
        self.settings = settings
        self.proxy_pool = proxy_pool
        self._default_retry_statuses = {429, 403, 503}

    @property
    def _http_backend(self) -> str:
        return str(getattr(self.settings, "http_backend", "httpx")).lower().strip()

    @property
    def _retry_statuses(self) -> set[int]:
        raw = getattr(self.settings, "request_retry_statuses", "")
        if not raw:
            return self._default_retry_statuses
        parsed: set[int] = set()
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                parsed.add(int(part))
            except ValueError:
                continue
        return parsed or self._default_retry_statuses

    @property
    def _auto_backend_order(self) -> list[str]:
        raw = str(getattr(self.settings, "http_backend_auto_order", "httpx,curl_cffi"))
        parsed = [item.strip().lower() for item in raw.split(",") if item.strip()]
        allowed = {"httpx", "curl_cffi"}
        order = [item for item in parsed if item in allowed]
        return order or ["httpx", "curl_cffi"]

    def _build_headers(self) -> dict[str, str]:
        ua = self.settings.user_agent
        ua_pool_raw = getattr(self.settings, "user_agent_pool", "")
        if ua_pool_raw:
            variants = [x.strip() for x in ua_pool_raw.split(",") if x.strip()]
            if variants:
                ua = random.choice(variants)
        headers = {"User-Agent": ua}
        if getattr(self.settings, "browser_headers_enabled", True):
            headers.update(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
        return headers

    async def _sleep_before_retry(self, attempt: int, retry_after: float | None = None) -> None:
        base_delay = float(getattr(self.settings, "request_delay_seconds", 1.0))
        backoff_multiplier = float(getattr(self.settings, "request_backoff_multiplier", 2.0))
        jitter_seconds = float(getattr(self.settings, "request_jitter_seconds", 0.3))
        max_backoff = float(getattr(self.settings, "request_max_backoff_seconds", 20.0))
        if retry_after is not None and retry_after > 0:
            delay = retry_after
        else:
            delay = min(max_backoff, base_delay * (backoff_multiplier**attempt))
        if jitter_seconds > 0:
            delay += random.uniform(0, jitter_seconds)
        await asyncio.sleep(delay)

    async def _request_httpx(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int) -> tuple[int, str, dict]:
        async with httpx.AsyncClient(
            timeout=timeout,
            proxy=proxy,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers)
        return response.status_code, response.text, dict(response.headers)

    async def _request_curl_cffi(
        self, url: str, headers: dict[str, str], proxy: str | None, timeout: int
    ) -> tuple[int, str, dict]:
        from curl_cffi.requests import AsyncSession

        impersonate = str(getattr(self.settings, "curl_impersonate", "chrome124"))
        async with AsyncSession() as client:
            response = await client.get(
                url,
                headers=headers,
                proxy=proxy,
                timeout=timeout,
                impersonate=impersonate,
                allow_redirects=True,
            )
        return int(response.status_code), str(response.text), dict(response.headers)

    async def _request_with_backend(
        self, url: str, headers: dict[str, str], proxy: str | None, timeout: int
    ) -> tuple[int, str, dict]:
        if self._http_backend == "auto":
            last_error: Exception | None = None
            for index, backend in enumerate(self._auto_backend_order):
                is_last = index == len(self._auto_backend_order) - 1
                try:
                    if backend == "curl_cffi":
                        status_code, response_text, response_headers = await self._request_curl_cffi(
                            url, headers, proxy, timeout
                        )
                    else:
                        status_code, response_text, response_headers = await self._request_httpx(url, headers, proxy, timeout)
                    if status_code in self._retry_statuses and not is_last:
                        # Continue through chain in the same attempt when anti-bot statuses appear.
                        continue
                    return status_code, response_text, response_headers
                except Exception as exc:
                    last_error = exc
                    if is_last:
                        raise
            if last_error is not None:
                raise last_error
            raise RuntimeError("No backend configured for auto mode")
        if self._http_backend == "curl_cffi":
            return await self._request_curl_cffi(url, headers, proxy, timeout)
        return await self._request_httpx(url, headers, proxy, timeout)

    async def get(self, url: str) -> str:
        attempts = self.settings.request_retries + 1
        timeout = self.settings.request_timeout
        rotate_proxy_on_retry = bool(getattr(self.settings, "proxy_rotate_on_retry", True))
        current_proxy = self.proxy_pool.next() if self.proxy_pool else None
        for attempt in range(attempts):
            if attempt > 0 and rotate_proxy_on_retry and self.proxy_pool:
                current_proxy = self.proxy_pool.next()
            headers = self._build_headers()
            try:
                status_code, response_text, response_headers = await self._request_with_backend(
                    url, headers=headers, proxy=current_proxy, timeout=timeout
                )
                if status_code in self._retry_statuses and attempt < attempts - 1:
                    retry_after_value = response_headers.get("Retry-After")
                    retry_after = None
                    if retry_after_value:
                        try:
                            retry_after = float(retry_after_value)
                        except ValueError:
                            retry_after = None
                    await self._sleep_before_retry(attempt, retry_after=retry_after)
                    continue
                if status_code >= 400:
                    raise RuntimeError(f"HTTP {status_code}")
                return response_text
            except Exception:
                if attempt == attempts - 1:
                    raise
                await self._sleep_before_retry(attempt)
        raise RuntimeError("Unreachable")
