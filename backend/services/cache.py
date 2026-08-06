"""Simple in-memory TTL cache keyed by ticker symbol."""
from __future__ import annotations

import time
from typing import Any, Optional
from config import CACHE_TTL_SECONDS


class TTLCache:
    def __init__(self, ttl: int = CACHE_TTL_SECONDS) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, ticker: str) -> Optional[Any]:
        if ticker not in self._store:
            return None
        val, expiry = self._store[ticker]
        if time.time() > expiry:
            del self._store[ticker]
            return None
        return val

    def get_meta(self, ticker: str) -> Optional[dict]:
        if ticker not in self._store:
            return None
        val, expiry = self._store[ticker]
        return {"ttl_remaining": max(0, expiry - time.time())}

    def set(self, ticker: str, value: Any) -> None:
        expiry = time.time() + self._ttl
        self._store[ticker] = (value, expiry)

    def delete(self, ticker: str) -> None:
        self._store.pop(ticker, None)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)

_cache = TTLCache()

def get(ticker: str) -> Optional[Any]:
    return _cache.get(ticker)

def get_meta(ticker: str) -> Optional[dict]:
    return _cache.get_meta(ticker)

def set(ticker: str, value: Any) -> None:
    _cache.set(ticker, value)

def delete(ticker: str) -> None:
    _cache.delete(ticker)

def clear() -> None:
    _cache.clear()

def size() -> int:
    return _cache.size()