#!/usr/bin/env python3
"""
Intelligent caching system for the Scrabbot dictionary.

This module implements:
- LRU (Least Recently Used) cache for frequent word lookups
- Intelligent preloading based on usage patterns
- Cache warming strategies
- Performance metrics and optimization
"""


import logging
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache replacement strategies."""

    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    TTL = "time_to_live"


@dataclass
class CacheEntry:
    """Entry in the cache with metadata."""

    value: Any
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    hit_rate: float = 0.0
    average_access_time_ms: float = 0.0
    preload_hits: int = 0

    def calculate_hit_rate(self):
        """Calculate and update hit rate."""
        total = self.hits + self.misses
        self.hit_rate = (self.hits / total * 100) if total > 0 else 0.0


class IntelligentCache:
    """
    High-performance intelligent cache with multiple strategies.

    Features:
    - Multiple eviction strategies (LRU, LFU, TTL)
    - Intelligent preloading based on patterns
    - Thread-safe operations
    - Performance analytics
    - Cache warming for common searches
    """

    def __init__(
        self,
        max_size: int = 10000,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: Optional[float] = None,
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl

        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._access_pattern: defaultdict[str, List[float]] = defaultdict(list)
        self._preload_candidates: Dict[str, float] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Statistics
        self.stats = CacheStats(max_size=max_size)

        logger.info(f"Intelligent cache initialized: {max_size} entries, {strategy.value} strategy")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        start_time = time.time()

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check expiration
                if entry.is_expired():
                    del self._cache[key]
                    self.stats.misses += 1
                    self.stats.evictions += 1
                    return None

                # Update access statistics
                entry.touch()
                self._record_access_pattern(key)

                # Move to end for LRU
                if self.strategy == CacheStrategy.LRU:
                    self._cache.move_to_end(key)

                self.stats.hits += 1
                elapsed_ms = (time.time() - start_time) * 1000
                self._update_access_time(elapsed_ms)

                return entry.value
            else:
                self.stats.misses += 1
                return None

    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (overrides default)
        """
        with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl if ttl is not None else self.default_ttl

            # Create new entry
            entry = CacheEntry(value=value, ttl_seconds=entry_ttl)

            # Check if key already exists
            if key in self._cache:
                # Update existing entry
                self._cache[key] = entry
                if self.strategy == CacheStrategy.LRU:
                    self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = entry

                # Evict if necessary
                if len(self._cache) > self.max_size:
                    self._evict_entry()

            self.stats.size = len(self._cache)

    def _evict_entry(self) -> None:
        """Evict an entry based on the configured strategy."""
        if not self._cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first item)
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]

        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            min_access_count = min(entry.access_count for entry in self._cache.values())
            for key, entry in self._cache.items():
                if entry.access_count == min_access_count:
                    del self._cache[key]
                    break

        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first, then oldest
            current_time = time.time()
            expired_keys = [key for key, entry in self._cache.items() if entry.ttl_seconds and (current_time - entry.created_at) > entry.ttl_seconds]

            if expired_keys:
                del self._cache[expired_keys[0]]
            else:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
                del self._cache[oldest_key]

        self.stats.evictions += 1

    def _record_access_pattern(self, key: str) -> None:
        """Record access pattern for intelligent preloading."""
        current_time = time.time()
        self._access_pattern[key].append(current_time)

        # Keep only recent accesses (last hour)
        hour_ago = current_time - 3600
        self._access_pattern[key] = [t for t in self._access_pattern[key] if t > hour_ago]

        # Update preload candidates
        if len(self._access_pattern[key]) >= 3:  # Frequently accessed
            self._preload_candidates[key] = current_time

    def _update_access_time(self, elapsed_ms: float) -> None:
        """Update average access time statistics."""
        total_accesses = self.stats.hits + self.stats.misses
        if total_accesses > 0:
            self.stats.average_access_time_ms = (self.stats.average_access_time_ms * (total_accesses - 1) + elapsed_ms) / total_accesses

    def preload_word(self, word: str, language: str, force: bool = False) -> bool:
        """
        Preload a word into the cache.

        Args:
            word: Word to preload
            language: Language code
            force: Force preload even if not in candidates

        Returns:
            True if preloaded, False if skipped
        """
        cache_key = f"{language}:{word}"

        if not force and cache_key not in self._preload_candidates:
            return False

        # This would typically fetch from database
        # For now, we'll simulate with a placeholder
        preloaded_data = {
            "word": word,
            "language": language,
            "preloaded": True,
            "timestamp": time.time(),
        }

        self.put(cache_key, preloaded_data, ttl=1800)  # 30 minutes TTL
        self.stats.preload_hits += 1

        return True

    def warm_cache(self, common_words: List[Tuple[str, str]]) -> int:
        """
        Warm the cache with commonly used words.

        Args:
            common_words: List of (word, language) tuples

        Returns:
            Number of words successfully warmed
        """
        warmed_count = 0

        for word, language in common_words:
            if self.preload_word(word, language, force=True):
                warmed_count += 1

        logger.info(f"Cache warmed with {warmed_count} words")
        return warmed_count

    def clear_expired(self) -> int:
        """
        Clear all expired entries from cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]

            for key in expired_keys:
                del self._cache[key]

            self.stats.size = len(self._cache)

            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")

            return len(expired_keys)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_pattern.clear()
            self._preload_candidates.clear()
            self.stats.size = 0
            logger.info("Cache cleared completely")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        self.stats.calculate_hit_rate()

        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate_percent": round(self.stats.hit_rate, 2),
            "evictions": self.stats.evictions,
            "current_size": self.stats.size,
            "max_size": self.stats.max_size,
            "utilization_percent": round((self.stats.size / self.stats.max_size) * 100, 2),
            "average_access_time_ms": round(self.stats.average_access_time_ms, 3),
            "preload_hits": self.stats.preload_hits,
            "strategy": self.strategy.value,
            "preload_candidates": len(self._preload_candidates),
            "access_patterns_tracked": len(self._access_pattern),
        }

    def get_top_accessed_words(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequently accessed words.

        Args:
            limit: Maximum number of results

        Returns:
            List of (key, access_count) tuples
        """
        with self._lock:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].access_count,
                reverse=True,
            )

            return [(key, entry.access_count) for key, entry in sorted_entries[:limit]]

    def optimize_cache(self) -> Dict[str, Any]:
        """
        Perform cache optimization operations.

        Returns:
            Optimization results
        """
        start_time = time.time()

        # Clear expired entries
        expired_cleared = self.clear_expired()

        # Identify optimal cache size based on access patterns
        active_entries = len([key for key, entry in self._cache.items() if entry.access_count > 1 and (time.time() - entry.last_access) < 1800])

        optimization_results = {
            "expired_entries_cleared": expired_cleared,
            "active_entries": active_entries,
            "recommended_cache_size": min(self.max_size, active_entries * 2),
            "optimization_time_ms": round((time.time() - start_time) * 1000, 2),
            "cache_efficiency": round((active_entries / self.stats.size) * 100, 2) if self.stats.size > 0 else 0,
        }

        logger.info(f"Cache optimization completed: {optimization_results}")
        return optimization_results


class DictionaryCacheManager:
    """
    High-level cache manager for dictionary operations.

    Manages separate caches for different types of operations:
    - Word validation cache
    - Definition cache
    - Search results cache
    """

    def __init__(self):
        # Separate caches for different operations
        self.word_cache = IntelligentCache(max_size=5000, strategy=CacheStrategy.LRU)
        self.definition_cache = IntelligentCache(max_size=3000, strategy=CacheStrategy.LRU, default_ttl=3600)
        self.search_cache = IntelligentCache(max_size=1000, strategy=CacheStrategy.TTL, default_ttl=600)

        logger.info("Dictionary cache manager initialized")

    def get_word_validation(self, word: str, language: str) -> Optional[Dict[str, Any]]:
        """Get cached word validation result."""
        cache_key = f"validation:{language}:{word.upper()}"
        return self.word_cache.get(cache_key)

    def cache_word_validation(self, word: str, language: str, result: Dict[str, Any]) -> None:
        """Cache word validation result."""
        cache_key = f"validation:{language}:{word.upper()}"
        self.word_cache.put(cache_key, result)

    def get_word_definition(self, word: str, language: str) -> Optional[str]:
        """Get cached word definition."""
        cache_key = f"definition:{language}:{word.upper()}"
        return self.definition_cache.get(cache_key)

    def cache_word_definition(self, word: str, language: str, definition: str) -> None:
        """Cache word definition."""
        cache_key = f"definition:{language}:{word.upper()}"
        self.definition_cache.put(cache_key, definition)

    def get_search_results(self, search_type: str, query: str, language: str) -> Optional[List[str]]:
        """Get cached search results."""
        cache_key = f"search:{search_type}:{language}:{query.upper()}"
        return self.search_cache.get(cache_key)

    def cache_search_results(self, search_type: str, query: str, language: str, results: List[str]) -> None:
        """Cache search results."""
        cache_key = f"search:{search_type}:{language}:{query.upper()}"
        self.search_cache.put(cache_key, results, ttl=300)  # 5 minutes for search results

    def get_combined_statistics(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return {
            "word_validation_cache": self.word_cache.get_statistics(),
            "definition_cache": self.definition_cache.get_statistics(),
            "search_cache": self.search_cache.get_statistics(),
            "total_memory_usage_estimate": (self.word_cache.stats.size + self.definition_cache.stats.size + self.search_cache.stats.size),
        }

    def warm_all_caches(self, common_words: List[Tuple[str, str]]) -> Dict[str, int]:
        """Warm all caches with common words."""
        return {
            "word_cache_warmed": self.word_cache.warm_cache(common_words),
            "definition_cache_warmed": self.definition_cache.warm_cache(common_words),
            "search_cache_warmed": self.search_cache.warm_cache(common_words),
        }


# Factory function
def create_cache_manager() -> DictionaryCacheManager:
    """Create and return a new cache manager."""
    return DictionaryCacheManager()
