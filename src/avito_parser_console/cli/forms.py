from __future__ import annotations

import questionary

from avito_parser_console.domain.models import FilterConfig, ParseRunRequest, SearchConfig


def _ask_int(prompt: str, default: str, min_value: int | None = None) -> int:
    while True:
        raw = questionary.text(prompt, default=default).ask() or default
        try:
            value = int(raw)
            if min_value is not None and value < min_value:
                raise ValueError
            return value
        except ValueError:
            print(f"Некорректное число: {raw}. Повторите ввод.")


def _ask_optional_int(prompt: str, default: str = "") -> int | None:
    while True:
        raw = questionary.text(prompt, default=default).ask() or ""
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print(f"Некорректное число: {raw}. Повторите ввод или оставьте пустым.")


def collect_run_request() -> ParseRunRequest:
    urls = questionary.text("URL поиска (через запятую):").ask() or ""
    page_limit = _ask_int("Макс страниц на запрос:", default="3", min_value=1)
    min_price = _ask_optional_int("Мин цена (пусто = нет):", default="")
    max_price = _ask_optional_int("Макс цена (пусто = нет):", default="")
    max_results_per_query = _ask_optional_int("Лимит объявлений на URL после фильтров (пусто = нет):", default="")

    return ParseRunRequest(
        search=SearchConfig(
            query_urls=[u.strip() for u in urls.split(",") if u.strip()],
            max_pages_per_query=page_limit,
        ),
        filters=FilterConfig(
            min_price=min_price,
            max_price=max_price,
            max_results_per_query=max_results_per_query,
        ),
    )
