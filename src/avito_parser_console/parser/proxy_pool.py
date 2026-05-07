from __future__ import annotations

from itertools import cycle


class ProxyPool:
    def __init__(self, proxies: list[str]):
        self._proxies = proxies
        self._iterator = cycle(proxies) if proxies else None

    def next(self) -> str | None:
        if not self._iterator:
            return None
        return next(self._iterator)
