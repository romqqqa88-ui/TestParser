from __future__ import annotations

import asyncio

import httpx

from avito_parser_console.config.settings import Settings
from avito_parser_console.parser.proxy_pool import ProxyPool


class AsyncHttpClient:
    def __init__(self, settings: Settings, proxy_pool: ProxyPool | None = None):
        self.settings = settings
        self.proxy_pool = proxy_pool

    async def get(self, url: str) -> str:
        headers = {"User-Agent": self.settings.user_agent}
        attempts = self.settings.request_retries + 1
        for attempt in range(attempts):
            proxy = self.proxy_pool.next() if self.proxy_pool else None
            try:
                async with httpx.AsyncClient(
                    timeout=self.settings.request_timeout,
                    proxy=proxy,
                    headers=headers,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception:
                if attempt == attempts - 1:
                    raise
                await asyncio.sleep(self.settings.request_delay_seconds * (attempt + 1))
        raise RuntimeError("Unreachable")
