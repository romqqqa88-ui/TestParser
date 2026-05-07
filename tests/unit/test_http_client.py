import pytest

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
