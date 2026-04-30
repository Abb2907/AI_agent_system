"""In-memory LRU cache for agent responses.

Caches final answers keyed by (query, history_hash) to avoid redundant LLM calls
for identical queries within the same conversation context.

Trade-off: Memory usage vs. latency/cost reduction.
- TTL-based expiration prevents stale answers
- Max size cap prevents unbounded memory growth
- Cache hit bypasses the full agent loop (planner + executor + LLM)
"""

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_MAX_SIZE = 128
DEFAULT_TTL_SECONDS = 300  # 5 minutes


@dataclass
class CacheEntry:
    value: dict
    created_at: float = field(default_factory=time.time)


class LRUCache:
    """Thread-safe LRU cache with TTL expiration.

    Design decisions:
    - OrderedDict gives O(1) access + LRU eviction
    - TTL prevents serving stale data when documents change
    - Size cap prevents OOM in long-running processes
    """

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, history: list[dict] | None) -> str:
        """Create a deterministic cache key from query + conversation context."""
        history_str = ""
        if history:
            # Only use last 5 messages for cache key (balance specificity vs. hit rate)
            recent = history[-5:]
            history_str = "|".join(f"{m['role']}:{m['content']}" for m in recent)
        raw = f"{query}||{history_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, history: list[dict] | None = None) -> dict | None:
        """Retrieve cached response if available and not expired."""
        key = self._make_key(query, history)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        # Check TTL
        if time.time() - entry.created_at > self._ttl:
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache entry expired for key {key[:8]}...")
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.info(f"Cache HIT (hits={self._hits}, misses={self._misses})")
        return entry.value

    def put(self, query: str, history: list[dict] | None, value: dict) -> None:
        """Store a response in the cache."""
        key = self._make_key(query, history)

        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(value=value)

    @property
    def stats(self) -> dict:
        """Return cache performance metrics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(hit_rate, 1),
        }


# Singleton instance
response_cache = LRUCache()
