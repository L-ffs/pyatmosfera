"""Cache em memória com validade (TTL) e tamanho máximo."""
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class TtlCache(Generic[T]):
    def __init__(self, ttl_seconds: int, max_size: int = 256,
                 clock: Callable[[], float] = time.time):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._clock = clock
        self._items: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._items[key]
            return None
        return value

    def set(self, key: str, value: T) -> None:
        if key not in self._items and len(self._items) >= self.max_size:
            self._purge()
            if len(self._items) >= self.max_size:
                oldest = min(self._items, key=lambda k: self._items[k][0])
                del self._items[oldest]
        self._items[key] = (self._clock() + self.ttl_seconds, value)

    def _purge(self) -> None:
        now = self._clock()
        for key in [k for k, (exp, _) in self._items.items() if now >= exp]:
            del self._items[key]
