from __future__ import annotations

from avito_parser_console.domain.models import FilterConfig, Listing, LogicMode
from avito_parser_console.filters.base import FilterRule
from avito_parser_console.filters.rules import AgeRule, FlagsRule, GeoRule, KeywordRule, PriceRule


class RuleEngine:
    def __init__(self, rules: list[FilterRule] | None = None):
        self.rules = rules or [PriceRule(), KeywordRule(), GeoRule(), AgeRule(), FlagsRule()]

    def apply(self, listings: list[Listing], config: FilterConfig) -> tuple[list[Listing], int]:
        passed, filtered_records = self.apply_with_report(listings, config)
        return passed, len(filtered_records)

    def evaluate(self, listing: Listing, config: FilterConfig) -> tuple[bool, list[str]]:
        checks = [rule.check(listing, config) for rule in self.rules]
        ok = all(checks) if config.logic_mode == LogicMode.AND else any(checks)
        failed = [rule.__class__.__name__ for rule, check in zip(self.rules, checks, strict=False) if not check]
        return ok, failed

    def apply_with_report(self, listings: list[Listing], config: FilterConfig) -> tuple[list[Listing], list[dict]]:
        passed: list[Listing] = []
        filtered_records: list[dict] = []
        for listing in listings:
            ok, failed = self.evaluate(listing, config)
            if ok:
                passed.append(listing)
            else:
                filtered_records.append(
                    {
                        "listing_id": listing.listing_id,
                        "url": str(listing.url),
                        "title": listing.title,
                        "reasons": failed,
                    }
                )
        return passed, filtered_records
