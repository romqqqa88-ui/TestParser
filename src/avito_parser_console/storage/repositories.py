from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from avito_parser_console.domain.models import Listing, RunStats
from avito_parser_console.storage.models import ListingDB, ParseRunDB


class ParseRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(self) -> int:
        run = ParseRunDB()
        self.session.add(run)
        await self.session.flush()
        return run.id

    async def complete_run(self, run_id: int, stats: RunStats) -> None:
        await self.session.execute(
            update(ParseRunDB)
            .where(ParseRunDB.id == run_id)
            .values(
                finished_at=datetime.now(timezone.utc),
                processed_pages=stats.processed_pages,
                found_listings=stats.found_listings,
                filtered_out=stats.filtered_out,
                saved_listings=stats.saved_listings,
                errors=stats.errors,
            )
        )


class ListingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_many(self, listings: list[Listing], run_id: int | None = None) -> int:
        if not listings:
            return 0
        values = []
        for item in listings:
            payload = item.model_dump(mode="json")
            payload["url"] = str(item.url)
            values.append(payload)
        stmt = insert(ListingDB).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_listing_id",
            set_={
                "title": stmt.excluded.title,
                "price": stmt.excluded.price,
                "area": stmt.excluded.area,
                "rooms": stmt.excluded.rooms,
                "floor": stmt.excluded.floor,
                "total_floors": stmt.excluded.total_floors,
                "address": stmt.excluded.address,
                "url": stmt.excluded.url,
                "published_at": stmt.excluded.published_at,
                "images": stmt.excluded.images,
                "seller_id": stmt.excluded.seller_id,
                "seller_name": stmt.excluded.seller_name,
                "views": stmt.excluded.views,
                "city": stmt.excluded.city,
                "district": stmt.excluded.district,
                "metro": stmt.excluded.metro,
                "is_reserved": stmt.excluded.is_reserved,
                "is_promoted": stmt.excluded.is_promoted,
                "raw": stmt.excluded.raw,
            },
        )
        await self.session.execute(stmt)
        return len(listings)

    async def fetch_for_export(self, limit: int = 1000) -> list[ListingDB]:
        res = await self.session.execute(select(ListingDB).order_by(ListingDB.updated_at.desc()).limit(limit))
        return list(res.scalars().all())
