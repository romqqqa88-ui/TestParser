$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/avito_parser"
}

if (-not $env:ALEMBIC_DATABASE_URL) {
  $env:ALEMBIC_DATABASE_URL = $env:DATABASE_URL -replace "\+asyncpg", ""
}

Write-Host "[smoke] Using DATABASE_URL=$($env:DATABASE_URL)"
Write-Host "[smoke] Using ALEMBIC_DATABASE_URL=$($env:ALEMBIC_DATABASE_URL)"

Write-Host "[smoke] Step 1/3: DB connectivity check"
@'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from avito_parser_console.config.settings import get_settings

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("[smoke] DB ok:", result.scalar())
    await engine.dispose()

asyncio.run(main())
'@ | python -

Write-Host "[smoke] Step 2/3: Alembic migration"
alembic upgrade head

Write-Host "[smoke] Step 3/3: Save -> export smoke"
@'
import asyncio
from avito_parser_console.config.settings import get_settings
from avito_parser_console.domain.models import Listing
from avito_parser_console.services.orchestrator import OrchestratorService
from avito_parser_console.storage.db import SessionLocal
from avito_parser_console.storage.repositories import ListingRepository

async def main():
    service = OrchestratorService(get_settings())
    async with SessionLocal() as session:
        listing = Listing(
            listing_id="smoke-script-1",
            title="Smoke квартира",
            price=7770000,
            area=40.0,
            rooms=2,
            address="Smoke address",
            url="https://www.avito.ru/smoke",
            city="Москва",
        )
        repo = ListingRepository(session)
        await repo.upsert_many([listing])
        await session.commit()

    async with SessionLocal() as session:
        xlsx = await service.export_latest(session, fmt="xlsx")
        csv = await service.export_latest(session, fmt="csv")
        jsn = await service.export_latest(session, fmt="json")
        print("[smoke] xlsx:", xlsx)
        print("[smoke] csv:", csv)
        print("[smoke] json:", jsn)

asyncio.run(main())
'@ | python -

Write-Host "[smoke] Completed successfully"
