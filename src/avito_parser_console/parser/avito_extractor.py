from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from avito_parser_console.domain.models import Listing


def _safe_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


class AvitoExtractor:
    def extract(self, html: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.select('script[type="mime/invalid"]')
        listings: list[Listing] = []
        for script in scripts:
            text = script.text.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            candidates = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(candidates, list):
                continue
            for item in candidates:
                parsed = self._to_listing(item)
                if parsed:
                    listings.append(parsed)
        return listings

    def _to_listing(self, item: dict[str, Any]) -> Listing | None:
        listing_id = str(item.get("id") or "")
        url = item.get("url")
        if not listing_id or not url:
            return None
        published_at = None
        ts = item.get("published_at")
        if isinstance(ts, (int, float)):
            published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
        return Listing(
            listing_id=listing_id,
            title=str(item.get("title") or ""),
            price=_safe_get(item, "price", default=None),
            area=_safe_get(item, "params", "area", default=None),
            rooms=_safe_get(item, "params", "rooms", default=None),
            floor=_safe_get(item, "params", "floor", default=None),
            total_floors=_safe_get(item, "params", "total_floors", default=None),
            address=item.get("address"),
            url=url,
            published_at=published_at,
            images=item.get("images") or [],
            seller_id=str(_safe_get(item, "seller", "id", default="")) or None,
            seller_name=_safe_get(item, "seller", "name", default=None),
            views=item.get("views"),
            city=_safe_get(item, "geo", "city", default=None),
            district=_safe_get(item, "geo", "district", default=None),
            metro=_safe_get(item, "geo", "metro", default=None),
            is_reserved=bool(item.get("is_reserved", False)),
            is_promoted=bool(item.get("is_promoted", False)),
            raw=item,
        )
