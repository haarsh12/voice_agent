"""Production-grade performance monitoring and metrics collection."""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, TypeVar

logger = logging.getLogger("sahayak.performance")

T = TypeVar("T")


@dataclass
class PerformanceMetrics:
    """Container for timing and performance metrics."""

    operation: str
    duration_ms: float
    success: bool
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def log(self, level: int = logging.INFO) -> None:
        """Log this metric at the specified level."""
        log_data = {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
        }
        
        if self.error_type:
            log_data["error_type"] = self.error_type
        
        if self.metadata:
            log_data.update(self.metadata)
        
        logger.log(
            level,
            "performance_metric %(operation)s duration_ms=%(duration_ms).2f success=%(success)s",
            log_data,
        )


@contextmanager
def measure_time(
    operation: str,
    *,
    log_level: int = logging.INFO,
    threshold_ms: float | None = None,
    **metadata: Any,
) -> Generator[PerformanceMetrics, None, None]:
    """Context manager to measure operation duration with automatic logging.
    
    Args:
        operation: Name of the operation being measured
        log_level: Logging level for the metric
        threshold_ms: If set, only log if duration exceeds this threshold
        **metadata: Additional metadata to include in the metric
    
    Usage:
        with measure_time("database_query", query_type="select"):
            result = await session.execute(query)
    """
    start_time = time.perf_counter()
    metric = PerformanceMetrics(
        operation=operation,
        duration_ms=0.0,
        success=True,
        metadata=metadata,
    )
    
    try:
        yield metric
    except Exception as e:
        metric.success = False
        metric.error_type = type(e).__name__
        raise
    finally:
        metric.duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Only log if threshold not set or exceeded
        if threshold_ms is None or metric.duration_ms >= threshold_ms:
            metric.log(level=log_level)


def measure_async(
    operation: str | None = None,
    *,
    log_level: int = logging.INFO,
    threshold_ms: float | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to measure async function performance.
    
    Args:
        operation: Operation name (defaults to function name)
        log_level: Logging level for the metric
        threshold_ms: Only log if duration exceeds this threshold
    
    Usage:
        @measure_async("user_retrieval")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with measure_time(op_name, log_level=log_level, threshold_ms=threshold_ms):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def measure_sync(
    operation: str | None = None,
    *,
    log_level: int = logging.INFO,
    threshold_ms: float | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to measure sync function performance.
    
    Args:
        operation: Operation name (defaults to function name)
        log_level: Logging level for the metric
        threshold_ms: Only log if duration exceeds this threshold
    
    Usage:
        @measure_sync("vector_search")
        def search_vectors(query: str):
            return vector_store.search(query)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with measure_time(op_name, log_level=log_level, threshold_ms=threshold_ms):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PerformanceTracker:
    """Track and aggregate performance metrics over time."""
    
    def __init__(self, name: str) -> None:
        self.name = name
        self._measurements: list[float] = []
        self._failures = 0
        self._start_time = time.time()
    
    def record(self, duration_ms: float, success: bool = True) -> None:
        """Record a single measurement."""
        self._measurements.append(duration_ms)
        if not success:
            self._failures += 1
    
    def get_stats(self) -> dict[str, Any]:
        """Get aggregated statistics."""
        if not self._measurements:
            return {
                "name": self.name,
                "count": 0,
                "failures": self._failures,
            }
        
        sorted_measurements = sorted(self._measurements)
        count = len(sorted_measurements)
        
        return {
            "name": self.name,
            "count": count,
            "failures": self._failures,
            "success_rate": (count - self._failures) / count if count > 0 else 0.0,
            "min_ms": sorted_measurements[0],
            "max_ms": sorted_measurements[-1],
            "mean_ms": sum(sorted_measurements) / count,
            "p50_ms": sorted_measurements[count // 2],
            "p95_ms": sorted_measurements[int(count * 0.95)] if count >= 20 else sorted_measurements[-1],
            "p99_ms": sorted_measurements[int(count * 0.99)] if count >= 100 else sorted_measurements[-1],
            "uptime_seconds": time.time() - self._start_time,
        }
    
    def log_stats(self, level: int = logging.INFO) -> None:
        """Log current statistics."""
        stats = self.get_stats()
        logger.log(
            level,
            "performance_stats %(name)s count=%(count)d p50_ms=%(p50_ms).2f p95_ms=%(p95_ms).2f success_rate=%(success_rate).2f%%",
            {**stats, "success_rate": stats.get("success_rate", 0) * 100},
        )
    
    def reset(self) -> None:
        """Reset all measurements."""
        self._measurements.clear()
        self._failures = 0
        self._start_time = time.time()


# Global trackers for key operations
_retrieval_tracker = PerformanceTracker("knowledge_retrieval")
_embedding_tracker = PerformanceTracker("embedding_generation")
_llm_tracker = PerformanceTracker("llm_inference")


def track_retrieval(duration_ms: float, success: bool = True) -> None:
    """Track a knowledge retrieval operation."""
    _retrieval_tracker.record(duration_ms, success)


def track_embedding(duration_ms: float, success: bool = True) -> None:
    """Track an embedding generation operation."""
    _embedding_tracker.record(duration_ms, success)


def track_llm(duration_ms: float, success: bool = True) -> None:
    """Track an LLM inference operation."""
    _llm_tracker.record(duration_ms, success)


def log_all_performance_stats(level: int = logging.INFO) -> None:
    """Log statistics for all tracked operations."""
    for tracker in [_retrieval_tracker, _embedding_tracker, _llm_tracker]:
        tracker.log_stats(level)


def get_all_performance_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all tracked operations."""
    return {
        "retrieval": _retrieval_tracker.get_stats(),
        "embedding": _embedding_tracker.get_stats(),
        "llm": _llm_tracker.get_stats(),
    }
