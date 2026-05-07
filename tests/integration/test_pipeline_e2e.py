import pytest

from avito_parser_console.parser.avito_extractor import AvitoExtractor
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
    assert result.stats.query_stats["https://www.avito.ru/moskva/kvartiry"]["processed_pages"] == 1
    assert result.stats.query_stats["https://www.avito.ru/moskva/kvartiry"]["passed_listings"] == 0
    assert result.stats.query_stats["https://www.avito.ru/moskva/kvartiry"]["filtered_out"] == 0


def test_extractor_parses_wrapped_json_payload():
    html = (
        '<script type="mime/invalid">window.__initialData = '
        '{"items":[{"id":"fixture-1","url":"https://www.avito.ru/item","title":"Квартира","price":123}]};</script>'
    )
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    assert listings[0].listing_id == "fixture-1"


def test_extractor_parses_html_fixture():
    with open("tests/fixtures/avito_search_sample.html", "r", encoding="utf-8") as fp:
        html = fp.read()
    listings = AvitoExtractor().extract(html)
    assert len(listings) == 1
    listing = listings[0]
    assert listing.listing_id == "sample-42"
    assert listing.city == "Москва"
    assert listing.metro == "Тверская"


@pytest.mark.asyncio
async def test_parser_runner_collects_filtered_records(monkeypatch):
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
        return (
            '<script type="mime/invalid">{"items":[{"id":"x1","url":"https://www.avito.ru/i","title":"x","price":100}]}</script>'
        )

    monkeypatch.setattr(service.http_client, "get", fake_get)
    request = ParseRunRequest(
        search=SearchConfig(query_urls=["https://www.avito.ru/moskva/kvartiry"], max_pages_per_query=1),
        filters=FilterConfig(min_price=1000),
    )
    result = await service.run(request)
    assert result.stats.filtered_out == 1
    assert len(result.filtered_out_records) == 1
    assert result.filtered_out_records[0]["listing_id"] == "x1"
    assert result.filtered_out_records[0]["query_url"] == "https://www.avito.ru/moskva/kvartiry"
    assert result.stats.query_stats["https://www.avito.ru/moskva/kvartiry"]["passed_listings"] == 0
    assert result.stats.query_stats["https://www.avito.ru/moskva/kvartiry"]["filtered_out"] == 1


@pytest.mark.asyncio
async def test_parser_runner_collects_query_level_errors(monkeypatch):
    class DummySettings:
        proxy_enabled = False
        proxy_list = ""
        request_timeout = 5
        request_retries = 0
        request_delay_seconds = 0
        max_pages_per_query = 1
        max_concurrency = 2
        user_agent = "ua"

    service = ParserRunnerService(DummySettings())

    async def fake_get(url: str) -> str:
        if "bad" in url:
            raise RuntimeError("network blocked")
        return '<script type="mime/invalid">{"items":[]}</script>'

    monkeypatch.setattr(service.http_client, "get", fake_get)
    request = ParseRunRequest(
        search=SearchConfig(
            query_urls=["https://www.avito.ru/good", "https://www.avito.ru/bad"],
            max_pages_per_query=1,
        ),
        filters=FilterConfig(),
    )
    result = await service.run(request)
    assert result.stats.errors == 1
    assert result.stats.query_stats["https://www.avito.ru/good"]["errors"] == 0
    assert result.stats.query_stats["https://www.avito.ru/bad"]["errors"] == 1
    assert result.stats.query_stats["https://www.avito.ru/good"]["passed_listings"] == 0
    assert result.stats.query_stats["https://www.avito.ru/good"]["filtered_out"] == 0
