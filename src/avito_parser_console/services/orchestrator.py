from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import ParseRunRequest, ParseRunResult
from avito_parser_console.export.csv_exporter import CsvExporter
from avito_parser_console.export.excel_exporter import ExcelExporter
from avito_parser_console.export.json_exporter import JsonExporter
from avito_parser_console.parser.runner import ParserRunnerService
from avito_parser_console.storage.repositories import ListingRepository, ParseRunRepository


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

        run_id = await run_repo.create_run()
        result = await self.parser.run(request)
        saved = await listing_repo.upsert_many(result.listings, run_id=run_id)
        result.stats.saved_listings = saved
        result.run_id = run_id
        await run_repo.complete_run(run_id, result.stats)
        await session.commit()
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

    @staticmethod
    def _db_row_to_dict(row: object) -> dict:
        return {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
