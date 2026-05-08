from __future__ import annotations

from avito_parser_console.cli.interactive import ask_checkbox, ask_select, ask_text, ask_confirm
from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import FilterConfig, LogicMode, ParseRunRequest, SearchConfig


def _ask_int(prompt: str, default: str, min_value: int | None = None) -> int:
    while True:
        raw = ask_text(prompt, default=default)
        try:
            value = int(raw)
            if min_value is not None and value < min_value:
                raise ValueError
            return value
        except ValueError:
            print(f"Некорректное число: {raw}. Повторите ввод.")


def _ask_optional_int(prompt: str, default: str = "") -> int | None:
    while True:
        raw = ask_text(prompt, default=default)
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print(f"Некорректное число: {raw}. Повторите ввод или оставьте пустым.")


def _ask_csv_list(prompt: str, default: str = "") -> list[str]:
    raw = ask_text(prompt, default=default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def collect_run_request(settings: Settings) -> ParseRunRequest:
    urls = ask_text("URL поиска (через запятую):", default="")
    default_pages = str(max(1, int(settings.max_pages_per_query)))
    page_limit = _ask_int("Макс страниц на запрос:", default=default_pages, min_value=1)
    selected_filters = ask_checkbox(
        "Какие фильтры применить?",
        choices=[
            "Цена",
            "Ключевые слова",
            "Гео (город/район/метро)",
            "Возраст объявления",
            "Скрыть reserved/promoted",
            "Чёрный список seller_id",
            "Лимит результатов",
        ],
    )

    min_price: int | None = None
    max_price: int | None = None
    include_keywords: list[str] = []
    exclude_keywords: list[str] = []
    cities: list[str] = []
    districts: list[str] = []
    metro_stations: list[str] = []
    max_age_hours: int | None = None
    exclude_reserved = True
    exclude_promoted = True
    seller_blacklist: list[str] = []
    max_results_per_query: int | None = None

    if "Цена" in selected_filters:
        min_price = _ask_optional_int("Мин цена (пусто = нет):", default="")
        max_price = _ask_optional_int("Макс цена (пусто = нет):", default="")

    if "Ключевые слова" in selected_filters:
        include_keywords = _ask_csv_list("Включать ключи (через запятую, пусто = нет):", default="")
        exclude_keywords = _ask_csv_list("Исключать ключи (через запятую, пусто = нет):", default="")

    if "Гео (город/район/метро)" in selected_filters:
        cities = _ask_csv_list("Города (через запятую, пусто = нет):", default="")
        districts = _ask_csv_list("Районы (через запятую, пусто = нет):", default="")
        metro_stations = _ask_csv_list("Метро (через запятую, пусто = нет):", default="")

    if "Возраст объявления" in selected_filters:
        max_age_hours = _ask_optional_int("Макс возраст в часах (пусто = нет):", default="")

    if "Скрыть reserved/promoted" in selected_filters:
        exclude_reserved = ask_confirm("Скрывать reserved?", default=True)
        exclude_promoted = ask_confirm("Скрывать promoted?", default=True)

    if "Чёрный список seller_id" in selected_filters:
        seller_blacklist = _ask_csv_list("seller_id blacklist (через запятую, пусто = нет):", default="")

    if "Лимит результатов" in selected_filters:
        max_results_per_query = _ask_optional_int("Лимит объявлений на URL после фильтров (пусто = нет):", default="")

    logic_mode_raw = ask_select(
        "Режим объединения правил:",
        choices=[LogicMode.AND.value, LogicMode.OR.value],
        default=LogicMode.AND.value,
    )

    return ParseRunRequest(
        search=SearchConfig(
            query_urls=[u.strip() for u in urls.split(",") if u.strip()],
            max_pages_per_query=page_limit,
        ),
        filters=FilterConfig(
            min_price=min_price,
            max_price=max_price,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            cities=cities,
            districts=districts,
            metro_stations=metro_stations,
            max_age_hours=max_age_hours,
            exclude_reserved=exclude_reserved,
            exclude_promoted=exclude_promoted,
            seller_blacklist=seller_blacklist,
            max_results_per_query=max_results_per_query,
            logic_mode=LogicMode(logic_mode_raw),
        ),
    )
