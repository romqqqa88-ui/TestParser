from __future__ import annotations

import json
import re
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
    _json_object_re = re.compile(r"\{.*\}", re.DOTALL)
    _rooms_re = re.compile(r"(\d+)\s*-\s*к\.", re.IGNORECASE)
    _area_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*м²", re.IGNORECASE)

    def extract(self, html: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.select('script[type="mime/invalid"]')
        listings: list[Listing] = []
        for script in scripts:
            text = script.text.strip()
            if not text:
                continue
            payload = self._parse_payload(text)
            if payload is None:
                continue
            listings.extend(self._extract_from_payload_tree(payload))
        if not listings:
            for script in soup.find_all("script"):
                text = script.text.strip()
                if len(text) < 50 or "items" not in text:
                    continue
                payload = self._parse_payload(text)
                if payload is None:
                    continue
                listings.extend(self._extract_from_payload_tree(payload))
                if listings:
                    break
        if not listings:
            listings.extend(self._extract_from_next_data(soup))
        return listings

    def _extract_from_next_data(self, soup: BeautifulSoup) -> list[Listing]:
        el = soup.select_one("script#__NEXT_DATA__")
        if not el:
            return []
        raw = (el.string if el.string is not None else el.get_text()).strip()
        if not raw:
            return []
        try:
            tree = json.loads(raw)
        except json.JSONDecodeError:
            return []
        best: list[Listing] = []
        for items in self._iter_candidate_item_lists(tree):
            parsed = [p for x in items if (p := self._to_listing(x))]
            if len(parsed) > len(best):
                best = parsed
        return best

    def _extract_from_payload_tree(self, tree: dict[str, Any]) -> list[Listing]:
        best: list[Listing] = []
        for items in self._iter_candidate_item_lists(tree):
            parsed = [p for x in items if (p := self._to_listing(x))]
            if len(parsed) > len(best):
                best = parsed
        return best

    @staticmethod
    def _looks_like_listing_items(items: list[Any]) -> bool:
        if not items or not isinstance(items, list):
            return False
        head = items[:10]
        required_valid = 1 if len(head) <= 3 else 3
        valid = 0
        for x in head:
            if not isinstance(x, dict):
                continue
            if not str(x.get("id") or "").strip():
                continue
            u = x.get("url") or x.get("urlPath")
            su = str(u or "").strip()
            if not su or (not su.startswith("/") and "avito.ru" not in su):
                continue
            if (
                x.get("price") is None
                and _safe_get(x, "priceDetailed", "value", default=None) is None
                and x.get("normalizedPrice") is None
                and x.get("sortTimeStamp") is None
            ):
                continue
            valid += 1
        return valid >= required_valid

    def _iter_candidate_item_lists(self, obj: Any, depth: int = 0) -> Any:
        if depth > 22:
            return
        if isinstance(obj, dict):
            for val in obj.values():
                if isinstance(val, list) and self._looks_like_listing_items(val):
                    yield val
                else:
                    yield from self._iter_candidate_item_lists(val, depth + 1)
        elif isinstance(obj, list):
            for x in obj:
                yield from self._iter_candidate_item_lists(x, depth + 1)

    def _parse_payload(self, text: str) -> dict[str, Any] | None:
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            match = self._json_object_re.search(text)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

    def _to_listing(self, item: dict[str, Any]) -> Listing | None:
        listing_id = str(item.get("id") or "")
        url = item.get("url") or item.get("urlPath")
        if not listing_id or not url:
            return None
        if isinstance(url, str) and url.startswith("/"):
            url = f"https://www.avito.ru{url}"
        published_at = None
        ts = item.get("published_at")
        if not isinstance(ts, (int, float)):
            ts = item.get("sortTimeStamp")
        if isinstance(ts, (int, float)):
            if ts > 1_000_000_000_000:
                ts = ts / 1000
            published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
        price = _safe_get(item, "price", default=None)
        if price is None:
            price = _safe_get(item, "priceDetailed", "value", default=None)
        if price is None:
            price = item.get("normalizedPrice")
        area = _safe_get(item, "params", "area", default=None)
        rooms = _safe_get(item, "params", "rooms", default=None)
        if (area is None or rooms is None) and isinstance(item.get("title"), str):
            parsed_rooms, parsed_area = self._parse_rooms_area_from_title(item["title"])
            if rooms is None:
                rooms = parsed_rooms
            if area is None:
                area = parsed_area
        try:
            return Listing(
                listing_id=listing_id,
                title=str(item.get("title") or ""),
                price=price,
                area=area,
                rooms=rooms,
                floor=_safe_get(item, "params", "floor", default=None),
                total_floors=_safe_get(item, "params", "total_floors", default=None),
                address=item.get("address") or _safe_get(item, "addressDetailed", "locationName", default=None),
                url=url,
                published_at=published_at,
                images=self._extract_image_urls(item.get("images")),
                seller_id=str(_safe_get(item, "seller", "id", default="")) or None,
                seller_name=_safe_get(item, "seller", "name", default=None),
                views=item.get("views"),
                city=_safe_get(item, "geo", "city", default=None),
                district=_safe_get(item, "geo", "district", default=None),
                metro=_safe_get(item, "geo", "metro", default=None),
                is_reserved=bool(item.get("is_reserved", item.get("isReserved", False))),
                is_promoted=bool(item.get("is_promoted", False)),
                raw=item,
            )
        except Exception:
            return None

    def _parse_rooms_area_from_title(self, title: str) -> tuple[int | None, float | None]:
        rooms: int | None = None
        area: float | None = None
        m_rooms = self._rooms_re.search(title)
        if m_rooms:
            try:
                rooms = int(m_rooms.group(1))
            except ValueError:
                rooms = None
        m_area = self._area_re.search(title)
        if m_area:
            try:
                area = float(m_area.group(1).replace(",", "."))
            except ValueError:
                area = None
        return rooms, area

    @staticmethod
    def _extract_image_urls(images: Any) -> list[str]:
        if not images:
            return []
        urls: list[str] = []
        if isinstance(images, list):
            for entry in images:
                if isinstance(entry, str):
                    if entry.startswith("http"):
                        urls.append(entry)
                    continue
                if isinstance(entry, dict):
                    for v in entry.values():
                        if isinstance(v, str) and v.startswith("http"):
                            urls.append(v)
        elif isinstance(images, dict):
            for v in images.values():
                if isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
        # Keep unique order
        seen: set[str] = set()
        out: list[str] = []
        for u in urls:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)
        return out
