"""Observability and metrics collection for the agent system.

Tracks:
- Request latency (end-to-end and per-component)
- Tool usage frequency and success rate
- Cache performance
- Error rates

Designed for easy integration with external monitoring (Prometheus, Datadog)
by exposing metrics as a JSON endpoint.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolMetric:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_duration_s: float = 0.0

    @property
    def avg_duration_s(self) -> float:
        return round(self.total_duration_s / self.calls, 3) if self.calls > 0 else 0.0

    @property
    def success_rate_pct(self) -> float:
        return round(self.successes / self.calls * 100, 1) if self.calls > 0 else 0.0


class MetricsCollector:
    """Collects and exposes system-wide metrics.

    All operations are append-only for thread safety in single-process deployments.
    For multi-process, replace with Redis-backed counters.
    """

    def __init__(self):
        self._request_count = 0
        self._total_latency_s = 0.0
        self._latencies: list[float] = []
        self._tool_metrics: dict[str, ToolMetric] = defaultdict(ToolMetric)
        self._error_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def record_request(self, duration_s: float) -> None:
        """Record a completed request with its latency."""
        self._request_count += 1
        self._total_latency_s += duration_s
        self._latencies.append(duration_s)
        # Keep only last 1000 for percentile calculation
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]

    def record_tool_call(self, tool_name: str, duration_s: float, success: bool) -> None:
        """Record a tool execution result."""
        metric = self._tool_metrics[tool_name]
        metric.calls += 1
        metric.total_duration_s += duration_s
        if success:
            metric.successes += 1
        else:
            metric.failures += 1

    def record_error(self) -> None:
        """Record an unhandled error."""
        self._error_count += 1

    def record_cache_hit(self) -> None:
        self._cache_hits += 1

    def record_cache_miss(self) -> None:
        self._cache_misses += 1

    @property
    def summary(self) -> dict:
        """Return a complete metrics summary."""
        avg_latency = (
            round(self._total_latency_s / self._request_count, 3)
            if self._request_count > 0
            else 0.0
        )

        # Calculate p50, p95, p99 latencies
        percentiles = {}
        if self._latencies:
            sorted_lat = sorted(self._latencies)
            n = len(sorted_lat)
            percentiles = {
                "p50_s": round(sorted_lat[int(n * 0.5)], 3),
                "p95_s": round(sorted_lat[int(n * 0.95)], 3),
                "p99_s": round(sorted_lat[min(int(n * 0.99), n - 1)], 3),
            }

        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = round(self._cache_hits / cache_total * 100, 1) if cache_total > 0 else 0.0

        return {
            "requests": {
                "total": self._request_count,
                "errors": self._error_count,
                "avg_latency_s": avg_latency,
                **percentiles,
            },
            "cache": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate_pct": cache_hit_rate,
            },
            "tools": {
                name: {
                    "calls": m.calls,
                    "success_rate_pct": m.success_rate_pct,
                    "avg_duration_s": m.avg_duration_s,
                }
                for name, m in self._tool_metrics.items()
            },
        }


# Singleton instance
metrics = MetricsCollector()
