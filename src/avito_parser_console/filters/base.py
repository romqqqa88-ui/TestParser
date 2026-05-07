from __future__ import annotations

from abc import ABC, abstractmethod

from avito_parser_console.domain.models import FilterConfig, Listing


class FilterRule(ABC):
    @abstractmethod
    def check(self, listing: Listing, config: FilterConfig) -> bool:
        raise NotImplementedError
