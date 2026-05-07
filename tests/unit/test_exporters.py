from datetime import UTC, datetime
from pathlib import Path

from avito_parser_console.export.excel_exporter import ExcelExporter
from avito_parser_console.export.json_exporter import JsonExporter


def test_excel_exporter_handles_timezone_datetime(tmp_path: Path):
    rows = [
        {
            "listing_id": "1",
            "title": "Тест",
            "published_at": datetime(2026, 5, 7, 21, 0, tzinfo=UTC),
        }
    ]
    path = ExcelExporter().export(rows, str(tmp_path))
    assert Path(path).exists()
    assert path.endswith(".xlsx")


def test_json_exporter_serializes_datetime(tmp_path: Path):
    rows = [{"listing_id": "1", "published_at": datetime(2026, 5, 7, 21, 0, tzinfo=UTC)}]
    path = JsonExporter().export(rows, str(tmp_path))
    content = Path(path).read_text(encoding="utf-8")
    assert "2026-05-07T21:00:00+00:00" in content
