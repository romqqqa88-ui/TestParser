import pytest

from avito_parser_console.cli.app import CliApp
from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import Listing, ParseRunResult, RunStats


@pytest.mark.asyncio
async def test_view_results_prints_human_readable_without_json_dump(monkeypatch):
    app = CliApp(Settings())
    app.last_result = ParseRunResult(
        stats=RunStats(
            found_listings=3,
            saved_listings=2,
            duplicate_dropped=1,
            errors=0,
            query_stats={
                "https://www.avito.ru/moskva/kvartiry": {
                    "processed_pages": 2,
                    "found_listings": 3,
                    "passed_listings": 2,
                    "duplicate_dropped": 1,
                    "filtered_out": 0,
                    "errors": 0,
                }
            },
        ),
        listings=[
            Listing(
                listing_id="l1",
                title="1-к квартира",
                price=8_500_000,
                rooms=1,
                area=34.5,
                address="Москва, ЦАО",
                url="https://www.avito.ru/moskva/kvartiry/l1",
            ),
            Listing(
                listing_id="l2",
                title="2-к квартира",
                price=12_000_000,
                rooms=2,
                area=56.0,
                address="Москва, САО",
                url="https://www.avito.ru/moskva/kvartiry/l2",
            ),
        ],
    )

    printed: list[str] = []
    actions = iter(["Просмотр результатов", "Выход"])

    def fake_main_menu() -> str:
        return next(actions)

    def fail_model_dump_json(*args, **kwargs):
        raise AssertionError("model_dump_json should not be called for view action")

    monkeypatch.setattr("avito_parser_console.cli.app.main_menu", fake_main_menu)
    monkeypatch.setattr("avito_parser_console.cli.app.ask_confirm", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        "avito_parser_console.domain.models.ParseRunResult.model_dump_json",
        fail_model_dump_json,
    )
    monkeypatch.setattr(app.console, "print", lambda message: printed.append(str(message)))

    await app.run()

    combined = "\n".join(printed)
    assert "Результаты последнего запуска" in combined
    assert "Найдено:" in combined
    assert "Статистика по запросам" in combined
    assert "Превью сохранённых объявлений" in combined
    assert "1-к квартира" in combined
    assert "https://www.avito.ru/moskva/kvartiry/l1" in combined
    assert "Run report:" not in combined
