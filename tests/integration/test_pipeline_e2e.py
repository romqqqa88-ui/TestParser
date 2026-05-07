import pytest

from avito_parser_console.domain.models import FilterConfig, ParseRunRequest, SearchConfig
from avito_parser_console.parser.runner import ParserRunnerService


@pytest.mark.asyncio
async def test_parser_runner_handles_empty(monkeypatch):
    class DummySettings:
        proxy_enabled = False
        proxy_list = ""
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        max_pages_per_query = 1
        max_concurrency = 1
        user_agent = "ua"

    service = ParserRunnerService(DummySettings())

    async def fake_get(url: str) -> str:
        return "<html></html>"

    monkeypatch.setattr(service.http_client, "get", fake_get)
    request = ParseRunRequest(
        search=SearchConfig(query_urls=["https://www.avito.ru/moskva/kvartiry"], max_pages_per_query=1),
        filters=FilterConfig(),
    )
    result = await service.run(request)
    assert result.stats.processed_pages == 1
    assert result.stats.found_listings == 0
