from __future__ import annotations

from pathlib import Path

import pandas as pd

from avito_parser_console.export.naming import build_export_filename


class CsvExporter:
    def export(self, rows: list[dict], export_dir: str, query_tag: str | None = None) -> str:
        path = Path(export_dir)
        path.mkdir(parents=True, exist_ok=True)
        filename = build_export_filename("avito_export", "csv", query_tag=query_tag)
        full_path = path / filename
        pd.DataFrame(rows).to_csv(full_path, index=False)
        return str(full_path)
