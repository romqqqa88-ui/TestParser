from __future__ import annotations

import asyncio

from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import ParseRunRequest, ParseRunResult, RunStats
from avito_parser_console.filters.engine import RuleEngine
from avito_parser_console.parser.avito_extractor import AvitoExtractor
from avito_parser_console.parser.http_client import AsyncHttpClient
from avito_parser_console.parser.proxy_pool import ProxyPool


class ParserRunnerService:
    def __init__(self, settings: Settings):
        proxies = [p.strip() for p in settings.proxy_list.split(",") if p.strip()] if settings.proxy_enabled else []
        self.http_client = AsyncHttpClient(settings, ProxyPool(proxies) if proxies else None)
        self.extractor = AvitoExtractor()
        self.filter_engine = RuleEngine()
        self.settings = settings

    async def run(self, request: ParseRunRequest) -> ParseRunResult:
        stats = RunStats()
        all_listings = []
        sem = asyncio.Semaphore(self.settings.max_concurrency)

        async def process_page(url: str) -> None:
            async with sem:
                html = await self.http_client.get(url)
                listings = self.extractor.extract(html)
                stats.processed_pages += 1
                stats.found_listings += len(listings)
                all_listings.extend(listings)

        tasks = []
        for base_url in request.search.query_urls:
            for page in range(1, request.search.max_pages_per_query + 1):
                sep = "&" if "?" in str(base_url) else "?"
                tasks.append(process_page(f"{base_url}{sep}p={page}"))
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except Exception:
                stats.errors += 1

        filtered, filtered_count = self.filter_engine.apply(all_listings, request.filters)
        stats.filtered_out = filtered_count
        return ParseRunResult(stats=stats, listings=filtered)
