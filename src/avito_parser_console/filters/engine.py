from __future__ import annotations

from avito_parser_console.domain.models import FilterConfig, Listing, LogicMode
from avito_parser_console.filters.base import FilterRule
from avito_parser_console.filters.rules import AgeRule, FlagsRule, GeoRule, KeywordRule, PriceRule


class RuleEngine:
    def __init__(self, rules: list[FilterRule] | None = None):
        self.rules = rules or [PriceRule(), KeywordRule(), GeoRule(), AgeRule(), FlagsRule()]

    def apply(self, listings: list[Listing], config: FilterConfig) -> tuple[list[Listing], int]:
        passed: list[Listing] = []
        filtered_out = 0
        for listing in listings:
            checks = [rule.check(listing, config) for rule in self.rules]
            ok = all(checks) if config.logic_mode == LogicMode.AND else any(checks)
            if ok:
                passed.append(listing)
            else:
                filtered_out += 1
        return passed, filtered_out
