from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from avito_parser_console.export.naming import build_export_filename


class JsonExporter:
    def export(self, rows: list[dict], export_dir: str, query_tag: str | None = None) -> str:
        path = Path(export_dir)
        path.mkdir(parents=True, exist_ok=True)
        filename = build_export_filename("avito_export", "json", query_tag=query_tag)
        full_path = path / filename
        full_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2, default=self._json_default),
            encoding="utf-8",
        )
        return str(full_path)

    @staticmethod
    def _json_default(value: object) -> str:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)
