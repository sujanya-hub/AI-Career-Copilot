from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    created_at: float
    payload: Any


class AnalysisCache:
    def __init__(self, ttl_seconds: int = 900, max_entries: int = 128) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._store: dict[str, CacheEntry] = {}

    def make_key(self, *parts: str) -> str:
        digest = hashlib.sha256()
        for part in parts:
            digest.update((part or "").encode("utf-8", errors="ignore"))
            digest.update(b"\x1f")
        return digest.hexdigest()

    def get(self, key: str) -> Any | None:
        self._prune()
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() - entry.created_at > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        return entry.payload

    def set(self, key: str, payload: Any) -> None:
        self._prune()
        if len(self._store) >= self.max_entries:
            oldest_key = min(self._store, key=lambda item: self._store[item].created_at)
            self._store.pop(oldest_key, None)
        self._store[key] = CacheEntry(created_at=time.time(), payload=payload)

    def _prune(self) -> None:
        now = time.time()
        expired = [
            key for key, entry in self._store.items()
            if now - entry.created_at > self.ttl_seconds
        ]
        for key in expired:
            self._store.pop(key, None)
