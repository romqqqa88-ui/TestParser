from __future__ import annotations

import traceback
from typing import Any

from rich.console import Console
from sqlalchemy import text
from sqlalchemy.engine import make_url

from avito_parser_console.cli.forms import collect_run_request
from avito_parser_console.cli.interactive import ask_confirm, ask_select
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
            try:
                action = main_menu()
                if not action:
                    self.console.print("[yellow]Ввод не получен. Возврат в меню.[/yellow]")
                    continue
                if action == "Выход":
                    self.console.print("[green]Завершение работы[/green]")
                    return
                if action == "Запуск парсинга":
                    request = collect_run_request(self.settings)
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
                        export_filtered = ask_confirm(
                            f"Экспортировать отчёт filtered_out ({len(self.last_result.filtered_out_records)} шт.)?",
                            default=False,
                        )
                        if export_filtered:
                            filtered_path = self.orchestrator.export_filtered_out(self.last_result, fmt="csv")
                            self.console.print(f"[green]Filtered отчёт:[/green] {filtered_path}")
                            summary_path = self.orchestrator.export_filtered_out_summary(self.last_result, fmt="csv")
                            self.console.print(f"[green]Filtered summary:[/green] {summary_path}")
                    export_run_report = ask_confirm(
                        "Экспортировать полный отчёт запуска (JSON)?",
                        default=False,
                    )
                    if export_run_report:
                        report_path = self.orchestrator.export_run_report(self.last_result)
                        self.console.print(f"[green]Run report:[/green] {report_path}")
                    export_query_stats = ask_confirm(
                        "Экспортировать per-query статистику?",
                        default=False,
                    )
                    if export_query_stats:
                        query_stats_path = self.orchestrator.export_query_stats(self.last_result, fmt="csv")
                        self.console.print(f"[green]Query stats report:[/green] {query_stats_path}")
                    if self.last_result.error_records:
                        export_errors = ask_confirm(
                            f"Экспортировать отчёт ошибок ({len(self.last_result.error_records)} шт.)?",
                            default=True,
                        )
                        if export_errors:
                            errors_path = self.orchestrator.export_errors(self.last_result, fmt="csv")
                            self.console.print(f"[green]Errors report:[/green] {errors_path}")
                elif action == "Проверка БД":
                    await self.check_database()
                elif action == "Экспорт":
                    fmt = ask_select("Формат экспорта", choices=["xlsx", "csv", "json"], default="xlsx")
                    if not fmt:
                        self.console.print("[yellow]Формат не выбран. Возврат в меню.[/yellow]")
                        continue
                    async with SessionLocal() as session:
                        path = await self.orchestrator.export_latest(session, fmt=fmt)
                    self.console.print(f"[green]Экспорт завершён:[/green] {path}")
                elif action == "Просмотр результатов":
                    if not self.last_result:
                        self.console.print("[yellow]Нет результатов текущей сессии[/yellow]")
                    else:
                        self._print_last_result()
                        export_report = ask_confirm(
                            "Экспортировать полный JSON-отчёт в файл?",
                            default=False,
                        )
                        if export_report:
                            report_path = self.orchestrator.export_run_report(self.last_result)
                            self.console.print(f"[green]Run report:[/green] {report_path}")
                else:
                    self.console.print("[yellow]Раздел в процессе разработки[/yellow]")
            except Exception as exc:
                self.console.print(f"[red]Ошибка во время выполнения:[/red] {exc}")
                self.console.print(traceback.format_exc())
                self.console.print("[yellow]Возврат в главное меню...[/yellow]")

    def _print_last_result(self, preview_limit: int = 10) -> None:
        result = self.last_result
        if result is None:
            self.console.print("[yellow]Нет результатов текущей сессии[/yellow]")
            return

        stats = result.stats
        self.console.print("[bold cyan]Результаты последнего запуска[/bold cyan]")
        self.console.print(
            f"Найдено: [bold]{stats.found_listings}[/bold] | "
            f"Сохранено: [bold]{stats.saved_listings}[/bold] | "
            f"Дубликаты: [bold]{stats.duplicate_dropped}[/bold] | "
            f"Ошибки: [bold]{stats.errors}[/bold]"
        )

        if stats.query_stats:
            self.console.print("[bold blue]Статистика по запросам:[/bold blue]")
            for query_url, values in stats.query_stats.items():
                self.console.print(
                    f"- [blue]{query_url}[/blue]: pages={self._safe_stat(values, 'processed_pages')}, "
                    f"found={self._safe_stat(values, 'found_listings')}, "
                    f"saved={self._safe_stat(values, 'passed_listings')}, "
                    f"dup={self._safe_stat(values, 'duplicate_dropped')}, "
                    f"filtered={self._safe_stat(values, 'filtered_out')}, "
                    f"errors={self._safe_stat(values, 'errors')}"
                )

        if not result.listings:
            self.console.print("[yellow]Сохранённых объявлений нет[/yellow]")
            return

        preview = result.listings[:preview_limit]
        self.console.print(f"[bold green]Превью сохранённых объявлений (до {preview_limit}):[/bold green]")
        for idx, item in enumerate(preview, 1):
            self.console.print(
                f"{idx}. [bold]{item.title or 'Без названия'}[/bold] | "
                f"{self._format_price(item.price)} | "
                f"{self._format_layout(item.rooms, item.area)} | "
                f"{item.address or 'Адрес не указан'} | "
                f"{item.url}"
            )

        if len(result.listings) > preview_limit:
            self.console.print(
                f"[yellow]Показаны первые {preview_limit} из {len(result.listings)} объявлений.[/yellow]"
            )

    @staticmethod
    def _safe_stat(values: dict[str, Any], key: str) -> int:
        value = values.get(key, 0)
        return int(value) if isinstance(value, int | float) else 0

    @staticmethod
    def _format_price(price: int | None) -> str:
        if price is None:
            return "Цена: н/д"
        return f"Цена: {price:,} руб.".replace(",", " ")

    @staticmethod
    def _format_layout(rooms: int | None, area: float | None) -> str:
        rooms_text = f"{rooms}-к" if rooms is not None else "комнатность н/д"
        if area is None:
            return f"{rooms_text}, площадь н/д"
        return f"{rooms_text}, {area:g} м2"

    async def check_database(self) -> None:
        db_target = self._format_database_target()
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            if db_target:
                self.console.print(f"[green]Подключение к БД успешно:[/green] {db_target}")
            else:
                self.console.print("[green]Подключение к БД успешно[/green]")
        except Exception as exc:
            if db_target:
                self.console.print(f"[red]Не удалось подключиться к БД ({db_target}):[/red] {exc}")
            else:
                self.console.print(f"[red]Не удалось подключиться к БД:[/red] {exc}")

    def _format_database_target(self) -> str | None:
        try:
            parsed = make_url(self.settings.database_url)
        except Exception:
            return None

        if not parsed.host or not parsed.database:
            return None

        if parsed.port:
            return f"{parsed.host}:{parsed.port}/{parsed.database}"
        return f"{parsed.host}/{parsed.database}"
