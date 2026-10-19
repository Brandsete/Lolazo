import asyncio
import time
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass
class CacheEntry:
    """Represents a cached item with absolute monotonic expiration."""

    value: Any
    expires_at: float
    created_at: float
    hits: int = 0


class InMemoryCache:
    """High-performance, thread-safe in-memory cache with configurable TTL.

    Supports LRU/FIFO eviction when max capacity is reached, and automatic
    expiry pruning on reads.
    """

    def __init__(self, max_entries: int = 2000, default_ttl: int = 300) -> None:
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._storage: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0

    def get(self, key: str) -> Any | None:
        """Synchronously get a value if it exists and has not expired."""
        entry = self._storage.get(key)
        if entry is None:
            self._misses += 1
            return None

        now = time.monotonic()
        if now > entry.expires_at:
            # Expired
            self._storage.pop(key, None)
            self._misses += 1
            return None

        entry.hits += 1
        self._hits += 1
        return entry.value

    async def aget(self, key: str) -> Any | None:
        """Asynchronously get a value with lock safety."""
        async with self._lock:
            return self.get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | float | None = None,
    ) -> None:
        """Synchronously store a value with optional custom TTL."""
        ttl = float(ttl_seconds if ttl_seconds is not None else self.default_ttl)
        now = time.monotonic()
        expires_at = now + max(0.0, ttl)

        if len(self._storage) >= self.max_entries and key not in self._storage:
            self._evict_candidates(now)

        self._storage[key] = CacheEntry(
            value=value,
            expires_at=expires_at,
            created_at=now,
            hits=0,
        )

    async def aset(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | float | None = None,
    ) -> None:
        """Asynchronously store a value with lock safety."""
        async with self._lock:
            self.set(key, value, ttl_seconds)

    def delete(self, key: str) -> bool:
        """Remove a single entry from cache."""
        return self._storage.pop(key, None) is not None

    async def adelete(self, key: str) -> bool:
        """Asynchronously delete an entry from cache."""
        async with self._lock:
            return self.delete(key)

    def clear(self) -> None:
        """Clear all cached entries and reset statistics."""
        self._storage.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def aclear(self) -> None:
        """Asynchronously clear all cached entries."""
        async with self._lock:
            self.clear()

    def cleanup_expired(self) -> int:
        """Purge all currently expired entries, returning the number removed."""
        now = time.monotonic()
        expired_keys = [
            k for k, entry in self._storage.items() if now > entry.expires_at
        ]
        for k in expired_keys:
            self._storage.pop(k, None)
        return len(expired_keys)

    def _evict_candidates(self, now: float) -> None:
        """Evict expired items first; if still over capacity, evict oldest items."""
        # 1. Purge expired
        expired = [k for k, v in self._storage.items() if now > v.expires_at]
        for k in expired:
            self._storage.pop(k, None)

        # 2. If still at or over capacity, evict 10% oldest items
        if len(self._storage) >= self.max_entries:
            to_remove = max(1, self.max_entries // 10)
            sorted_keys = sorted(
                self._storage.keys(),
                key=lambda k: self._storage[k].created_at,
            )
            for k in sorted_keys[:to_remove]:
                self._storage.pop(k, None)
                self._evictions += 1

    def stats(self) -> dict[str, Any]:
        """Return operational cache metrics."""
        return {
            "size": len(self._storage),
            "max_entries": self.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
        }


# Global in-memory cache instance initialized from settings
cache = InMemoryCache(
    max_entries=settings.CACHE_MAX_ENTRIES,
    default_ttl=settings.CACHE_TTL_SECONDS,
)


# Helper functions to build consistent, collision-free cache keys
def build_profile_key(region: str, game_name: str, tag_line: str) -> str:
    """Build unique key for player profile caching."""
    reg = region.lower().strip()
    name = game_name.lower().strip()
    tag = tag_line.lower().strip()
    return f"profile:{reg}:{name}:{tag}"


def build_league_key(platform_id: str, summoner_id: str) -> str:
    """Build unique key for league competitive entries caching."""
    return f"league:{platform_id.lower().strip()}:{summoner_id.strip()}"


def build_match_key(cluster: str, match_id: str) -> str:
    """Build unique key for immutable match detail caching."""
    return f"match:{cluster.lower().strip()}:{match_id.lower().strip()}"


def build_match_ids_key(
    cluster: str, puuid: str, count: int, queue: str | None = None
) -> str:
    """Build unique key for player match IDs list caching."""
    q_str = queue.lower().strip() if queue else "all"
    return f"match_ids:{cluster.lower().strip()}:{puuid.strip()}:{count}:{q_str}"


def build_stats_key(
    region: str, game_name: str, tag_line: str, queue: str, matches: int
) -> str:
    """Build unique key for consolidated stats caching."""
    reg = region.lower().strip()
    name = game_name.lower().strip()
    tag = tag_line.lower().strip()
    q = queue.lower().strip()
    return f"stats:{reg}:{name}:{tag}:{q}:{matches}"


def build_champions_key(
    region: str, game_name: str, tag_line: str, matches: int
) -> str:
    """Build unique key for champions breakdown caching."""
    reg = region.lower().strip()
    name = game_name.lower().strip()
    tag = tag_line.lower().strip()
    return f"champions:{reg}:{name}:{tag}:{matches}"


def build_roles_key(region: str, game_name: str, tag_line: str, matches: int) -> str:
    """Build unique key for role distribution caching."""
    reg = region.lower().strip()
    name = game_name.lower().strip()
    tag = tag_line.lower().strip()
    return f"roles:{reg}:{name}:{tag}:{matches}"


def build_matches_summary_key(
    region: str, game_name: str, tag_line: str, count: int
) -> str:
    """Build unique key for matches summary list caching."""
    reg = region.lower().strip()
    name = game_name.lower().strip()
    tag = tag_line.lower().strip()
    return f"matches_summary:{reg}:{name}:{tag}:{count}"

