from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import ParseRunRequest, ParseRunResult
from avito_parser_console.export.csv_exporter import CsvExporter
from avito_parser_console.export.excel_exporter import ExcelExporter
from avito_parser_console.export.json_exporter import JsonExporter
from avito_parser_console.parser.runner import ParserRunnerService
from avito_parser_console.storage.repositories import ListingRepository, ParseRunRepository

T = TypeVar("T")


class OrchestratorService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = ParserRunnerService(settings)
        self.excel = ExcelExporter()
        self.csv = CsvExporter()
        self.json = JsonExporter()

    async def run_parse(self, request: ParseRunRequest, session: AsyncSession) -> ParseRunResult:
        run_repo = ParseRunRepository(session)
        listing_repo = ListingRepository(session)

        run_id = await self._run_with_db_retry(run_repo.create_run, session=session)
        result = await self.parser.run(request)
        
        async def _persist() -> tuple[int, list]:
            existing_ids = await listing_repo.existing_listing_ids([x.listing_id for x in result.listings])
            new_listings = [x for x in result.listings if x.listing_id not in existing_ids]
            saved = await listing_repo.upsert_many(result.listings, run_id=run_id)
            result.stats.saved_listings = saved
            result.run_id = run_id
            await run_repo.complete_run(run_id, result.stats)
            await session.commit()
            return saved, new_listings

        _, new_listings = await self._run_with_db_retry(_persist, session=session)
        self._append_new_listings_log(new_listings, run_id=run_id)
        return result

    async def export_latest(self, session: AsyncSession, fmt: str = "xlsx") -> str:
        listing_repo = ListingRepository(session)
        rows = [self._db_row_to_dict(row) for row in await listing_repo.fetch_for_export()]
        if fmt == "csv":
            return self.csv.export(rows, self.settings.export_dir)
        if fmt == "json":
            return self.json.export(rows, self.settings.export_dir)
        header_map = {
            "listing_id": "ID объявления",
            "title": "Заголовок",
            "price": "Цена",
            "area": "Площадь",
            "rooms": "Комнат",
            "address": "Адрес",
            "url": "Ссылка",
            "published_at": "Дата публикации",
        }
        return self.excel.export(rows, self.settings.export_dir, header_map=header_map)

    def export_filtered_out(self, result: ParseRunResult, fmt: str = "csv") -> str:
        rows = result.filtered_out_records
        if fmt == "json":
            return self.json.export(rows, self.settings.export_dir, query_tag="filtered_out")
        if fmt == "xlsx":
            return self.excel.export(rows, self.settings.export_dir, query_tag="filtered_out")
        return self.csv.export(rows, self.settings.export_dir, query_tag="filtered_out")

    def export_filtered_out_summary(self, result: ParseRunResult, fmt: str = "csv") -> str:
        rows = [
            {"rule": rule, "count": count}
            for rule, count in sorted(result.filtered_out_summary.items(), key=lambda item: item[1], reverse=True)
        ]
        if fmt == "json":
            return self.json.export(rows, self.settings.export_dir, query_tag="filtered_summary")
        if fmt == "xlsx":
            return self.excel.export(rows, self.settings.export_dir, query_tag="filtered_summary")
        return self.csv.export(rows, self.settings.export_dir, query_tag="filtered_summary")

    def export_errors(self, result: ParseRunResult, fmt: str = "csv") -> str:
        rows = result.error_records
        if fmt == "json":
            return self.json.export(rows, self.settings.export_dir, query_tag="errors")
        if fmt == "xlsx":
            return self.excel.export(rows, self.settings.export_dir, query_tag="errors")
        return self.csv.export(rows, self.settings.export_dir, query_tag="errors")

    def export_query_stats(self, result: ParseRunResult, fmt: str = "csv") -> str:
        rows = [{"query_url": query_url, **stats} for query_url, stats in result.stats.query_stats.items()]
        if fmt == "json":
            return self.json.export(rows, self.settings.export_dir, query_tag="query_stats")
        if fmt == "xlsx":
            return self.excel.export(rows, self.settings.export_dir, query_tag="query_stats")
        return self.csv.export(rows, self.settings.export_dir, query_tag="query_stats")

    def export_run_report(self, result: ParseRunResult) -> str:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_id": result.run_id,
            "stats": result.stats.model_dump(),
            "errors_count": len(result.error_records),
            "filtered_out_summary": result.filtered_out_summary,
            "filtered_out_count": len(result.filtered_out_records),
            "listings_count": len(result.listings),
        }
        return self.json.export([report], self.settings.export_dir, query_tag="run_report")

    @staticmethod
    def _db_row_to_dict(row: object) -> dict:
        return {k: v for k, v in row.__dict__.items() if not k.startswith("_")}

    def _append_new_listings_log(self, listings: list, run_id: int) -> None:
        path_raw = str(getattr(self.settings, "new_listings_file", "") or "").strip()
        if not path_raw or not listings:
            return
        path = Path(path_raw)
        if not path.is_absolute():
            path = Path(self.settings.export_dir) / path
        path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        write_jsonl = path.suffix.lower() == ".jsonl"
        with path.open("a", encoding="utf-8") as f:
            for item in listings:
                if write_jsonl:
                    row = {
                        "logged_at": now,
                        "run_id": run_id,
                        "listing_id": item.listing_id,
                        "title": item.title,
                        "price": item.price,
                        "rooms": item.rooms,
                        "area": item.area,
                        "url": str(item.url),
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    continue
                f.write(
                    f"{now}\trun={run_id}\tid={item.listing_id}\tprice={item.price}\trooms={item.rooms}\tarea={item.area}\turl={item.url}\ttitle={item.title}\n"
                )

    async def _run_with_db_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        session: AsyncSession | None = None,
    ) -> T:
        retries = max(0, int(getattr(self.settings, "db_retries", 2)))
        base_delay = max(0.0, float(getattr(self.settings, "db_retry_delay_seconds", 0.5)))
        backoff = max(1.0, float(getattr(self.settings, "db_retry_backoff_multiplier", 2.0)))
        jitter = max(0.0, float(getattr(self.settings, "db_retry_jitter_seconds", 0.2)))
        for attempt in range(retries + 1):
            try:
                return await operation()
            except Exception as exc:
                can_retry = attempt < retries and self._is_transient_db_error(exc)
                if not can_retry:
                    raise
                if session is not None:
                    try:
                        await session.rollback()
                    except Exception:
                        pass
                delay = base_delay * (backoff**attempt)
                if jitter > 0:
                    delay += random.uniform(0, jitter)
                await asyncio.sleep(delay)
        raise RuntimeError("Unreachable")

    @staticmethod
    def _is_transient_db_error(exc: Exception) -> bool:
        return isinstance(exc, (ConnectionError, ConnectionResetError, TimeoutError, OSError, DBAPIError, OperationalError, InterfaceError))
