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
        query_stats: dict[str, dict[str, int]] = {
            str(url): {"processed_pages": 0, "found_listings": 0, "errors": 0} for url in request.search.query_urls
        }

        async def process_page(query_url: str, page_url: str) -> None:
            async with sem:
                try:
                    html = await self.http_client.get(page_url)
                    listings = self.extractor.extract(html)
                    stats.processed_pages += 1
                    stats.found_listings += len(listings)
                    query_stats[query_url]["processed_pages"] += 1
                    query_stats[query_url]["found_listings"] += len(listings)
                    all_listings.extend(listings)
                except Exception:
                    query_stats[query_url]["errors"] += 1
                    raise

        tasks = []
        for base_url in request.search.query_urls:
            query_url = str(base_url)
            for page in range(1, request.search.max_pages_per_query + 1):
                sep = "&" if "?" in query_url else "?"
                tasks.append(process_page(query_url, f"{query_url}{sep}p={page}"))
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except Exception:
                stats.errors += 1

        filtered, filtered_records = self.filter_engine.apply_with_report(all_listings, request.filters)
        stats.filtered_out = len(filtered_records)
        stats.query_stats = query_stats
        return ParseRunResult(stats=stats, listings=filtered, filtered_out_records=filtered_records)
