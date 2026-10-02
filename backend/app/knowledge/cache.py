"""Production-grade caching layer for knowledge retrieval with TTL and LRU eviction."""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, Generic, TypeVar

logger = logging.getLogger("sahayak.knowledge.cache")

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Thread-safe cache entry with TTL and access tracking."""

    value: T
    created_at: float
    accessed_at: float
    access_count: int


class TTLCache(Generic[T]):
    """Thread-safe LRU cache with time-to-live and comprehensive metrics.
    
    Features:
    - LRU eviction when size limit reached
    - TTL expiration for stale entries
    - Thread-safe for concurrent access
    - Hit/miss metrics tracking
    - Memory-efficient OrderedDict implementation
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 1800,  # 30 minutes default
        name: str = "unnamed",
    ) -> None:
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = RLock()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.name = name

        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    def get(self, key: str) -> T | None:
        """Retrieve value if present and not expired, update LRU order."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]
            now = time.time()

            # Check TTL expiration
            if now - entry.created_at > self.ttl_seconds:
                del self._cache[key]
                self._expirations += 1
                self._misses += 1
                logger.debug(
                    "cache_expiration cache=%s key_hash=%s age_seconds=%d",
                    self.name,
                    key[:12],
                    int(now - entry.created_at),
                )
                return None

            # Update access tracking and move to end (most recent)
            entry.accessed_at = now
            entry.access_count += 1
            self._cache.move_to_end(key)
            self._hits += 1

            return entry.value

    def set(self, key: str, value: T) -> None:
        """Store value with current timestamp, evict LRU if at capacity."""
        with self._lock:
            now = time.time()

            # Update existing entry
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.created_at = now
                entry.accessed_at = now
                self._cache.move_to_end(key)
                return

            # Evict LRU item if at capacity
            if len(self._cache) >= self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug(
                    "cache_eviction cache=%s evicted_key_hash=%s reason=capacity",
                    self.name,
                    oldest_key[:12],
                )

            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                accessed_at=now,
                access_count=0,
            )

    def invalidate(self, key: str) -> bool:
        """Remove specific entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries from cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info("cache_cleared cache=%s entries=%d", self.name, count)

    def cleanup_expired(self) -> int:
        """Remove all expired entries, return count removed."""
        with self._lock:
            now = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if now - entry.created_at > self.ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
                self._expirations += 1

            if expired_keys:
                logger.debug(
                    "cache_cleanup cache=%s removed=%d",
                    self.name,
                    len(expired_keys),
                )
            return len(expired_keys)

    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        with self._lock:
            return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as percentage (0.0 to 1.0)."""
        with self._lock:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0

    def get_metrics(self) -> dict[str, Any]:
        """Get comprehensive cache metrics."""
        with self._lock:
            total_requests = self._hits + self._misses
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "hit_rate": self.hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
            }

    def __repr__(self) -> str:
        return (
            f"TTLCache(name={self.name}, size={self.size}/{self.max_size}, "
            f"hit_rate={self.hit_rate:.2%})"
        )


def make_cache_key(*parts: str | int | None) -> str:
    """Create consistent cache key from multiple components.
    
    Args:
        *parts: Key components (query, language, state, etc.)
    
    Returns:
        MD5 hash of concatenated parts
    """
    content = ":".join(str(p) if p is not None else "" for p in parts)
    return hashlib.md5(content.encode("utf-8")).hexdigest()


class RetrievalCache:
    """Specialized cache for knowledge retrieval results.
    
    Caches both successful retrievals and empty results to avoid
    repeated expensive vector searches.
    """

    def __init__(
        self,
        max_size: int = 2000,
        ttl_minutes: int = 30,
    ) -> None:
        self._cache = TTLCache[Any](
            max_size=max_size,
            ttl_seconds=ttl_minutes * 60,
            name="retrieval",
        )

    def get(
        self,
        query: str,
        language: str,
        user_state: str | None = None,
        user_district: str | None = None,
    ) -> Any | None:
        """Retrieve cached result if available."""
        key = make_cache_key(query.strip().lower(), language, user_state, user_district)
        return self._cache.get(key)

    def set(
        self,
        query: str,
        language: str,
        result: Any,
        user_state: str | None = None,
        user_district: str | None = None,
    ) -> None:
        """Store retrieval result in cache."""
        key = make_cache_key(query.strip().lower(), language, user_state, user_district)
        self._cache.set(key, result)

    def invalidate_language(self, language: str) -> int:
        """Invalidate all cache entries for a specific language (expensive)."""
        # This is a simplified version - for production, consider adding
        # language-specific sub-caches
        return 0

    def cleanup(self) -> int:
        """Remove expired entries."""
        return self._cache.cleanup_expired()

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        return self._cache.get_metrics()

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


class EmbeddingCache:
    """Cache for query embeddings to avoid re-embedding identical queries."""

    def __init__(
        self,
        max_size: int = 5000,
        ttl_minutes: int = 60,  # Embeddings can be cached longer
    ) -> None:
        self._cache = TTLCache[list[float]](
            max_size=max_size,
            ttl_seconds=ttl_minutes * 60,
            name="embedding",
        )

    def get(self, query: str, language: str = "") -> list[float] | None:
        """Retrieve cached embedding vector."""
        key = make_cache_key(query.strip().lower(), language)
        return self._cache.get(key)

    def set(self, query: str, embedding: list[float], language: str = "") -> None:
        """Store embedding vector in cache."""
        key = make_cache_key(query.strip().lower(), language)
        self._cache.set(key, embedding)

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        return self._cache.get_metrics()

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


# Global cache instances - initialized on first import
_retrieval_cache: RetrievalCache | None = None
_embedding_cache: EmbeddingCache | None = None


def get_retrieval_cache() -> RetrievalCache:
    """Get or create the global retrieval cache instance."""
    global _retrieval_cache
    if _retrieval_cache is None:
        _retrieval_cache = RetrievalCache(max_size=2000, ttl_minutes=30)
        logger.info("retrieval_cache_initialized max_size=2000 ttl_minutes=30")
    return _retrieval_cache


def get_embedding_cache() -> EmbeddingCache:
    """Get or create the global embedding cache instance."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(max_size=5000, ttl_minutes=60)
        logger.info("embedding_cache_initialized max_size=5000 ttl_minutes=60")
    return _embedding_cache


def log_cache_metrics() -> None:
    """Log metrics for all active caches (useful for monitoring)."""
    if _retrieval_cache:
        metrics = _retrieval_cache.get_metrics()
        logger.info(
            "cache_metrics type=retrieval size=%d/%d hit_rate=%.2f%% hits=%d misses=%d",
            metrics["size"],
            metrics["max_size"],
            metrics["hit_rate"] * 100,
            metrics["hits"],
            metrics["misses"],
        )
    
    if _embedding_cache:
        metrics = _embedding_cache.get_metrics()
        logger.info(
            "cache_metrics type=embedding size=%d/%d hit_rate=%.2f%% hits=%d misses=%d",
            metrics["size"],
            metrics["max_size"],
            metrics["hit_rate"] * 100,
            metrics["hits"],
            metrics["misses"],
        )
