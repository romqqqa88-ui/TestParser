from __future__ import annotations

import questionary
from rich.console import Console

from avito_parser_console.cli.forms import collect_run_request
from avito_parser_console.cli.menus import main_menu
from avito_parser_console.config.settings import Settings
from avito_parser_console.services.orchestrator import OrchestratorService
from avito_parser_console.storage.db import SessionLocal


class CliApp:
    def __init__(self, settings: Settings):
        self.console = Console()
        self.settings = settings
        self.orchestrator = OrchestratorService(settings)
        self.last_result = None

    async def run(self) -> None:
        while True:
            action = main_menu()
            if action == "Выход":
                self.console.print("[green]Завершение работы[/green]")
                return
            if action == "Запуск парсинга":
                request = collect_run_request()
                async with SessionLocal() as session:
                    self.console.print("[cyan]Парсинг запущен...[/cyan]")
                    self.last_result = await self.orchestrator.run_parse(request, session)
                    self.console.print(
                        f"[green]Готово.[/green] Найдено: {self.last_result.stats.found_listings}, "
                        f"Дубликаты: {self.last_result.stats.duplicate_dropped}, "
                        f"Сохранено: {self.last_result.stats.saved_listings}, Ошибок: {self.last_result.stats.errors}"
                    )
                    for query_url, values in self.last_result.stats.query_stats.items():
                        self.console.print(
                            f"[blue]{query_url}[/blue] pages={values['processed_pages']} "
                            f"found={values['found_listings']} dup={values['duplicate_dropped']} passed={values['passed_listings']} "
                            f"filtered={values['filtered_out']} capped={values['capped_out']} errors={values['errors']}"
                        )
                if self.last_result.filtered_out_records:
                    if self.last_result.filtered_out_summary:
                        summary_text = ", ".join(
                            f"{rule}: {count}" for rule, count in self.last_result.filtered_out_summary.items()
                        )
                        self.console.print(f"[magenta]Причины отсева:[/magenta] {summary_text}")
                    export_filtered = questionary.confirm(
                        f"Экспортировать отчёт filtered_out ({len(self.last_result.filtered_out_records)} шт.)?",
                        default=False,
                    ).ask()
                    if export_filtered:
                        filtered_path = self.orchestrator.export_filtered_out(self.last_result, fmt="csv")
                        self.console.print(f"[green]Filtered отчёт:[/green] {filtered_path}")
                        summary_path = self.orchestrator.export_filtered_out_summary(self.last_result, fmt="csv")
                        self.console.print(f"[green]Filtered summary:[/green] {summary_path}")
                export_run_report = questionary.confirm(
                    "Экспортировать полный отчёт запуска (JSON)?",
                    default=False,
                ).ask()
                if export_run_report:
                    report_path = self.orchestrator.export_run_report(self.last_result)
                    self.console.print(f"[green]Run report:[/green] {report_path}")
            elif action == "Экспорт":
                fmt = (
                    questionary.select("Формат экспорта", choices=["xlsx", "csv", "json"], default="xlsx").ask()
                    or "xlsx"
                )
                async with SessionLocal() as session:
                    path = await self.orchestrator.export_latest(session, fmt=fmt)
                self.console.print(f"[green]Экспорт завершён:[/green] {path}")
            elif action == "Просмотр результатов":
                if not self.last_result:
                    self.console.print("[yellow]Нет результатов текущей сессии[/yellow]")
                else:
                    self.console.print(self.last_result.model_dump_json(indent=2))
            else:
                self.console.print("[yellow]Раздел в процессе разработки[/yellow]")
