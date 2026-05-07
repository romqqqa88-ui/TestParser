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
                        f"Сохранено: {self.last_result.stats.saved_listings}, Ошибок: {self.last_result.stats.errors}"
                    )
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
