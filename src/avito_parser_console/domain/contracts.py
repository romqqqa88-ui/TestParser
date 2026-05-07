from __future__ import annotations

from typing import Protocol

from avito_parser_console.domain.models import FilterConfig, Listing, ParseRunRequest, ParseRunResult


class ParserRunner(Protocol):
    async def run(self, request: ParseRunRequest) -> ParseRunResult: ...


class FilterEngine(Protocol):
    def apply(self, listings: list[Listing], config: FilterConfig) -> tuple[list[Listing], int]: ...


class ListingRepository(Protocol):
    async def upsert_many(self, listings: list[Listing], run_id: int | None = None) -> int: ...
