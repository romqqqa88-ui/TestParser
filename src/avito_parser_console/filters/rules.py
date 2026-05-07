from __future__ import annotations

from datetime import datetime, timedelta, timezone

from avito_parser_console.domain.models import FilterConfig, Listing
from avito_parser_console.filters.base import FilterRule


class PriceRule(FilterRule):
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        if listing.price is None:
            return False
        if config.min_price is not None and listing.price < config.min_price:
            return False
        if config.max_price is not None and listing.price > config.max_price:
            return False
        return True


class KeywordRule(FilterRule):
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        text = f"{listing.title} {listing.address or ''}".lower()
        if config.include_keywords and not any(k.lower() in text for k in config.include_keywords):
            return False
        if any(k.lower() in text for k in config.exclude_keywords):
            return False
        return True


class GeoRule(FilterRule):
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        if config.cities and (listing.city or "").lower() not in {x.lower() for x in config.cities}:
            return False
        if config.districts and (listing.district or "").lower() not in {x.lower() for x in config.districts}:
            return False
        if config.metro_stations and (listing.metro or "").lower() not in {x.lower() for x in config.metro_stations}:
            return False
        return True


class AgeRule(FilterRule):
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        if config.max_age_hours is None or listing.published_at is None:
            return True
        threshold = datetime.now(timezone.utc) - timedelta(hours=config.max_age_hours)
        return listing.published_at >= threshold


class FlagsRule(FilterRule):
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        if config.exclude_reserved and listing.is_reserved:
            return False
        if config.exclude_promoted and listing.is_promoted:
            return False
        if listing.seller_id and listing.seller_id in set(config.seller_blacklist):
            return False
        return True
