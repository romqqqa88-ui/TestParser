from __future__ import annotations

import questionary

from avito_parser_console.domain.models import FilterConfig, ParseRunRequest, SearchConfig


def collect_run_request() -> ParseRunRequest:
    urls = questionary.text("URL поиска (через запятую):").ask() or ""
    page_limit = int(questionary.text("Макс страниц на запрос:", default="3").ask() or "3")
    min_price = questionary.text("Мин цена (пусто = нет):", default="").ask() or None
    max_price = questionary.text("Макс цена (пусто = нет):", default="").ask() or None

    return ParseRunRequest(
        search=SearchConfig(
            query_urls=[u.strip() for u in urls.split(",") if u.strip()],
            max_pages_per_query=page_limit,
        ),
        filters=FilterConfig(
            min_price=int(min_price) if min_price else None,
            max_price=int(max_price) if max_price else None,
        ),
    )
