from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from avito_parser_console.domain.models import ParseRunRequest
from avito_parser_console.services.orchestrator import OrchestratorService


async def run_parse_job(
    request: ParseRunRequest,
    orchestrator: OrchestratorService,
    session_factory: async_sessionmaker,
) -> None:
    logger.info("Scheduled parse job started")
    async with session_factory() as session:
        result = await orchestrator.run_parse(request, session)
    logger.info(
        "Scheduled parse job finished: pages={}, found={}, saved={}, errors={}",
        result.stats.processed_pages,
        result.stats.found_listings,
        result.stats.saved_listings,
        result.stats.errors,
    )
