import json
from datetime import datetime, timezone

import pytest

from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import Listing, ParseRunResult, RunStats
from avito_parser_console.services.orchestrator import OrchestratorService


def test_export_filtered_out_summary_creates_csv(tmp_path):
    settings = Settings(export_dir=str(tmp_path))
    service = OrchestratorService(settings)
    result = ParseRunResult(
        stats=RunStats(),
        filtered_out_summary={"PriceRule": 3, "GeoRule": 1},
    )
    path = service.export_filtered_out_summary(result, fmt="csv")
    assert path.endswith(".csv")


def test_export_run_report_creates_json(tmp_path):
    settings = Settings(export_dir=str(tmp_path))
    service = OrchestratorService(settings)
    result = ParseRunResult(
        run_id=42,
        stats=RunStats(processed_pages=3, found_listings=10),
        filtered_out_summary={"PriceRule": 2},
    )
    path = service.export_run_report(result)
    assert path.endswith(".json")


def test_export_errors_creates_csv(tmp_path):
    settings = Settings(export_dir=str(tmp_path))
    service = OrchestratorService(settings)
    result = ParseRunResult(
        stats=RunStats(),
        error_records=[{"query_url": "u", "page_url": "p", "error": "e"}],
    )
    path = service.export_errors(result, fmt="csv")
    assert path.endswith(".csv")


def test_export_query_stats_creates_csv(tmp_path):
    settings = Settings(export_dir=str(tmp_path))
    service = OrchestratorService(settings)
    result = ParseRunResult(
        stats=RunStats(
            query_stats={
                "https://www.avito.ru/a": {
                    "processed_pages": 1,
                    "found_listings": 2,
                    "duplicate_dropped": 0,
                    "passed_listings": 2,
                    "filtered_out": 0,
                    "capped_out": 0,
                    "errors": 0,
                }
            }
        )
    )
    path = service.export_query_stats(result, fmt="csv")
    assert path.endswith(".csv")


def test_append_new_listings_log_writes_file(tmp_path):
    settings = Settings(export_dir=str(tmp_path), new_listings_file="new_listings.log")
    service = OrchestratorService(settings)
    listing = Listing(
        listing_id="n1",
        title="1-к квартира",
        price=100,
        rooms=1,
        area=30.0,
        url="https://www.avito.ru/moskva/kvartiry/test",
        published_at=datetime.now(timezone.utc),
    )
    service._append_new_listings_log([listing], run_id=7)
    log_path = tmp_path / "new_listings.log"
    assert log_path.exists()
    text = log_path.read_text(encoding="utf-8")
    assert "run=7" in text
    assert "id=n1" in text


def test_append_new_listings_log_writes_jsonl_when_extension_is_jsonl(tmp_path):
    settings = Settings(export_dir=str(tmp_path), new_listings_file="new_listings.jsonl")
    service = OrchestratorService(settings)
    listing = Listing(
        listing_id="n2",
        title="2-к квартира",
        price=200,
        rooms=2,
        area=55.5,
        url="https://www.avito.ru/moskva/kvartiry/test2",
        published_at=datetime.now(timezone.utc),
    )
    service._append_new_listings_log([listing], run_id=8)
    log_path = tmp_path / "new_listings.jsonl"
    assert log_path.exists()
    line = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["run_id"] == 8
    assert payload["listing_id"] == "n2"
    assert payload["price"] == 200


@pytest.mark.asyncio
async def test_run_with_db_retry_retries_transient_errors(monkeypatch, tmp_path):
    settings = Settings(export_dir=str(tmp_path), db_retries=2, db_retry_delay_seconds=0.0, db_retry_jitter_seconds=0.0)
    service = OrchestratorService(settings)
    calls = {"count": 0}

    async def fake_sleep(_: float) -> None:
        return None

    async def flaky_op() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionResetError("temporary disconnect")
        return "ok"

    monkeypatch.setattr("avito_parser_console.services.orchestrator.asyncio.sleep", fake_sleep)
    result = await service._run_with_db_retry(flaky_op)
    assert result == "ok"
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_run_with_db_retry_does_not_retry_non_transient(tmp_path):
    settings = Settings(export_dir=str(tmp_path), db_retries=3, db_retry_delay_seconds=0.0, db_retry_jitter_seconds=0.0)
    service = OrchestratorService(settings)
    calls = {"count": 0}

    async def bad_op() -> None:
        calls["count"] += 1
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        await service._run_with_db_retry(bad_op)
    assert calls["count"] == 1
