from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from avito_parser_console.config.settings import get_settings
from avito_parser_console.domain.models import FilterConfig, ParseRunRequest, SearchConfig
from avito_parser_console.services.orchestrator import OrchestratorService
from avito_parser_console.storage.db import SessionLocal


async def main() -> None:
    settings = get_settings()
    request = ParseRunRequest(
        search=SearchConfig(query_urls=["https://www.avito.ru/moskva/kvartiry"], max_pages_per_query=1),
        filters=FilterConfig(),
    )
    async with SessionLocal() as session:
        result = await OrchestratorService(settings).run_parse(request, session)
    print(
        datetime.now(timezone.utc).isoformat(),
        "found",
        result.stats.found_listings,
        "saved",
        result.stats.saved_listings,
        "errors",
        result.stats.errors,
    )


if __name__ == "__main__":
    asyncio.run(main())
