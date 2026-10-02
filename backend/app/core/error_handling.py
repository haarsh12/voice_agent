"""Production-grade error handling with context preservation and recovery."""

from __future__ import annotations

import functools
import logging
import traceback
from typing import Any, Callable, TypeVar

logger = logging.getLogger("sahayak.errors")

T = TypeVar("T")


class SahayakError(Exception):
    """Base exception for all Sahayak-specific errors."""

    def __init__(
        self,
        message: str,
        *,
        user_message: str | None = None,
        error_code: str | None = None,
        recoverable: bool = True,
        **context: Any,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.user_message = user_message or "An error occurred. Please try again."
        self.error_code = error_code
        self.recoverable = recoverable
        self.context = context


class KnowledgeRetrievalError(SahayakError):
    """Error during knowledge retrieval operations."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(
            message,
            user_message="Could not retrieve information at this time.",
            error_code="KNOWLEDGE_RETRIEVAL_FAILED",
            recoverable=True,
            **context,
        )


class DatabaseError(SahayakError):
    """Error during database operations."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(
            message,
            user_message="A database error occurred. Please try again shortly.",
            error_code="DATABASE_ERROR",
            recoverable=True,
            **context,
        )


class VectorSearchError(SahayakError):
    """Error during vector search operations."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(
            message,
            user_message="Search service temporarily unavailable.",
            error_code="VECTOR_SEARCH_FAILED",
            recoverable=True,
            **context,
        )


class EmbeddingError(SahayakError):
    """Error during embedding generation."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(
            message,
            user_message="Could not process your query. Please try again.",
            error_code="EMBEDDING_FAILED",
            recoverable=True,
            **context,
        )


class ConfigurationError(SahayakError):
    """Error in system configuration."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(
            message,
            user_message="System configuration error. Please contact support.",
            error_code="CONFIGURATION_ERROR",
            recoverable=False,
            **context,
        )


def log_error(
    error: Exception,
    operation: str,
    *,
    level: int = logging.ERROR,
    include_traceback: bool = True,
    **context: Any,
) -> None:
    """Log an error with context and optional traceback.
    
    Args:
        error: The exception to log
        operation: Name of the operation that failed
        level: Logging level
        include_traceback: Whether to include full traceback
        **context: Additional context to log
    """
    error_data = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context,
    }
    
    # Add custom error attributes if present
    if isinstance(error, SahayakError):
        error_data["error_code"] = error.error_code
        error_data["recoverable"] = error.recoverable
        error_data.update(error.context)
    
    logger.log(
        level,
        "operation_failed %(operation)s error_type=%(error_type)s message=%(error_message)s",
        error_data,
    )
    
    if include_traceback:
        logger.debug("Error traceback: %s", traceback.format_exc())


def handle_errors(
    operation: str,
    *,
    fallback_value: Any = None,
    re_raise: bool = False,
    log_level: int = logging.ERROR,
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """Decorator to handle errors in functions with logging and fallback.
    
    Args:
        operation: Name of the operation for logging
        fallback_value: Value to return on error (if not re-raising)
        re_raise: Whether to re-raise the exception after logging
        log_level: Logging level for errors
    
    Usage:
        @handle_errors("user_lookup", fallback_value=None)
        async def get_user(user_id: int):
            return await db.get(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                log_error(error, operation, level=log_level)
                if re_raise:
                    raise
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as error:
                log_error(error, operation, level=log_level)
                if re_raise:
                    raise
                return fallback_value
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def safe_operation(
    operation: str,
    default: T,
    *,
    log_failure: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that guarantees a function returns a value, never raises.
    
    Args:
        operation: Operation name for logging
        default: Default value to return on any error
        log_failure: Whether to log failures
    
    Usage:
        @safe_operation("cache_lookup", default={})
        def get_from_cache(key: str):
            return cache[key]  # May raise KeyError
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as error:
                if log_failure:
                    log_error(
                        error,
                        operation,
                        level=logging.WARNING,
                        include_traceback=False,
                    )
                return default
        
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for operations that should never crash the application.
    
    Usage:
        with ErrorContext("background_cleanup", suppress=True):
            cleanup_old_files()  # Won't crash if it fails
    """
    
    def __init__(
        self,
        operation: str,
        *,
        suppress: bool = True,
        log_level: int = logging.ERROR,
        **context: Any,
    ) -> None:
        self.operation = operation
        self.suppress = suppress
        self.log_level = log_level
        self.context = context
    
    def __enter__(self) -> ErrorContext:
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is None:
            return False
        
        log_error(
            exc_val,
            self.operation,
            level=self.log_level,
            **self.context,
        )
        
        return self.suppress


def validate_not_none(value: T | None, name: str) -> T:
    """Validate that a value is not None, raise descriptive error if it is.
    
    Args:
        value: Value to check
        name: Name of the value for error message
    
    Returns:
        The value if not None
    
    Raises:
        ValueError: If value is None
    """
    if value is None:
        raise ValueError(f"{name} must not be None")
    return value


def validate_positive(value: int | float, name: str) -> int | float:
    """Validate that a numeric value is positive.
    
    Args:
        value: Value to check
        name: Name of the value for error message
    
    Returns:
        The value if positive
    
    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_in_range(
    value: int | float,
    min_val: int | float,
    max_val: int | float,
    name: str,
) -> int | float:
    """Validate that a value is within a specified range.
    
    Args:
        value: Value to check
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        name: Name of the value for error message
    
    Returns:
        The value if in range
    
    Raises:
        ValueError: If value is out of range
    """
    if not min_val <= value <= max_val:
        raise ValueError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )
    return value
