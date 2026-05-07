from avito_parser_console.config.settings import Settings
from avito_parser_console.domain.models import ParseRunResult, RunStats
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
