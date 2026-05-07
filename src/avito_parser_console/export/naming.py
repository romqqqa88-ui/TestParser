from __future__ import annotations

from datetime import datetime


def build_export_filename(prefix: str, ext: str, query_tag: str | None = None) -> str:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"_{query_tag}" if query_tag else ""
    return f"{prefix}{tag}_{now}.{ext}"
