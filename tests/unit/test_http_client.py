import pytest
from datetime import datetime, timezone

from avito_parser_console.parser.http_client import AsyncHttpClient


@pytest.mark.asyncio
async def test_http_client_retries_on_429(monkeypatch):
    class DummySettings:
        request_timeout = 5
        request_retries = 1
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True

    class DummyResponse:
        def __init__(self, status_code: int, text: str = "", headers: dict | None = None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"status={self.status_code}")

    class DummyClient:
        def __init__(self):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, headers: dict | None = None):
            self.calls += 1
            if self.calls == 1:
                return DummyResponse(429, headers={"Retry-After": "0"})
            return DummyResponse(200, text="ok")

    dummy_client = DummyClient()

    def fake_async_client(*args, **kwargs):
        return dummy_client

    async def fake_sleep(seconds: float):
        return None

    monkeypatch.setattr("avito_parser_console.parser.http_client.httpx.AsyncClient", fake_async_client)
    monkeypatch.setattr("avito_parser_console.parser.http_client.asyncio.sleep", fake_sleep)

    client = AsyncHttpClient(DummySettings())
    response_text = await client.get("https://example.com")
    assert response_text == "ok"
    assert dummy_client.calls == 2


@pytest.mark.asyncio
async def test_http_client_uses_curl_backend(monkeypatch):
    class DummySettings:
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True
        http_backend = "curl_cffi"
        curl_impersonate = "chrome124"
        proxy_rotate_on_retry = True

    async def fake_request_curl(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int):
        return 200, "curl_ok", {}

    monkeypatch.setattr(AsyncHttpClient, "_request_curl_cffi", fake_request_curl)
    client = AsyncHttpClient(DummySettings())
    response_text = await client.get("https://example.com")
    assert response_text == "curl_ok"


@pytest.mark.asyncio
async def test_http_client_auto_backend_falls_back_to_curl(monkeypatch):
    class DummySettings:
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True
        http_backend = "auto"
        curl_impersonate = "chrome124"
        proxy_rotate_on_retry = True

    async def fake_request_httpx(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int):
        return 429, "blocked", {}

    async def fake_request_curl(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int):
        return 200, "auto_ok", {}

    monkeypatch.setattr(AsyncHttpClient, "_request_httpx", fake_request_httpx)
    monkeypatch.setattr(AsyncHttpClient, "_request_curl_cffi", fake_request_curl)
    client = AsyncHttpClient(DummySettings())
    response_text = await client.get("https://example.com")
    assert response_text == "auto_ok"


@pytest.mark.asyncio
async def test_http_client_auto_backend_respects_order(monkeypatch):
    class DummySettings:
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True
        http_backend = "auto"
        http_backend_auto_order = "curl_cffi,httpx"
        curl_impersonate = "chrome124"
        proxy_rotate_on_retry = True

    calls: list[str] = []

    async def fake_request_httpx(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int):
        calls.append("httpx")
        return 200, "httpx_ok", {}

    async def fake_request_curl(self, url: str, headers: dict[str, str], proxy: str | None, timeout: int):
        calls.append("curl_cffi")
        return 429, "blocked", {}

    monkeypatch.setattr(AsyncHttpClient, "_request_httpx", fake_request_httpx)
    monkeypatch.setattr(AsyncHttpClient, "_request_curl_cffi", fake_request_curl)
    client = AsyncHttpClient(DummySettings())
    response_text = await client.get("https://example.com")
    assert response_text == "httpx_ok"
    assert calls == ["curl_cffi", "httpx"]


def test_parse_retry_after_http_date():
    class DummySettings:
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True

    client = AsyncHttpClient(DummySettings())
    now = datetime(2026, 5, 7, 19, 45, 0, tzinfo=timezone.utc)
    delay = client._parse_retry_after("Thu, 07 May 2026 19:45:05 GMT", now=now)
    assert delay == 5.0


def test_parse_retry_after_invalid_value():
    class DummySettings:
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        request_backoff_multiplier = 1.0
        request_jitter_seconds = 0.0
        request_max_backoff_seconds = 1.0
        request_retry_statuses = "429"
        user_agent = "ua"
        user_agent_pool = ""
        browser_headers_enabled = True

    client = AsyncHttpClient(DummySettings())
    delay = client._parse_retry_after("not-a-valid-retry-after")
    assert delay is None
