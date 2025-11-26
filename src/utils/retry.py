"""
Retry logic with exponential backoff for network operations.

Features:
- Configurable retry attempts
- Exponential backoff with jitter
- Retry-ability detection
- Timeout handling
"""

import time
import logging
import functools
from typing import Callable, Type, Tuple, Optional, Any
from random import uniform

from ..exceptions import (
    SecurityAuditException,
    NetworkError,
    is_retryable,
    get_severity,
    ErrorSeverity
)

logger = logging.getLogger(__name__)


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)

    if jitter:
        # Add jitter: random value between 0 and 25% of delay
        jitter_amount = uniform(0, delay * 0.25)
        delay += jitter_amount

    return delay


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (NetworkError,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retryable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback called on each retry attempt

    Example:
        @retry_with_backoff(max_retries=5)
        def fetch_from_rpc(url: str) -> Dict:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    # Check if this specific exception is retryable
                    if not is_retryable(e):
                        logger.warning(
                            f"{func.__name__} failed with non-retryable error: {e}"
                        )
                        raise

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries"
                        )
                        raise

                    # Calculate backoff delay
                    delay = exponential_backoff(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay
                    )

                    # Log retry attempt
                    severity = get_severity(e)
                    log_level = logging.WARNING if severity in (
                        ErrorSeverity.HIGH,
                        ErrorSeverity.CRITICAL
                    ) else logging.INFO

                    logger.log(
                        log_level,
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s. Error: {e}"
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.warning(
                                f"Retry callback failed: {callback_error}"
                            )

                    # Wait before retry
                    time.sleep(delay)

                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"{func.__name__} failed with error: {e}")
                    raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for retry operations.

    Example:
        with RetryContext(max_retries=3) as retry:
            for attempt in retry:
                try:
                    result = risky_operation()
                    break
                except NetworkError as e:
                    if not retry.should_retry(e):
                        raise
                    retry.wait()
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (NetworkError,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions
        self.attempt = 0
        self.last_exception: Optional[Exception] = None

    def __enter__(self):
        """Enter retry context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit retry context."""
        return False

    def __iter__(self):
        """Iterate through retry attempts."""
        self.attempt = 0
        return self

    def __next__(self):
        """Get next retry attempt."""
        if self.attempt > self.max_retries:
            raise StopIteration

        current = self.attempt
        self.attempt += 1
        return current

    def should_retry(self, exception: Exception) -> bool:
        """
        Check if exception should be retried.

        Args:
            exception: Exception to check

        Returns:
            True if should retry
        """
        self.last_exception = exception

        # Check if we've exhausted retries
        if self.attempt > self.max_retries:
            return False

        # Check if exception type is retryable
        if not isinstance(exception, self.retryable_exceptions):
            return False

        # Check if specific exception instance is retryable
        return is_retryable(exception)

    def wait(self):
        """Wait before next retry with exponential backoff."""
        delay = exponential_backoff(
            self.attempt - 1,  # -1 because we already incremented
            base_delay=self.base_delay,
            max_delay=self.max_delay
        )

        if self.last_exception:
            logger.info(
                f"Retry attempt {self.attempt}/{self.max_retries + 1}, "
                f"waiting {delay:.2f}s. Error: {self.last_exception}"
            )

        time.sleep(delay)


def retry_on_failure(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    error_message: str = "Operation failed",
    **kwargs
) -> Any:
    """
    Execute operation with retry logic.

    Args:
        operation: Callable to execute
        max_retries: Maximum retry attempts
        base_delay: Base delay between retries
        error_message: Error message for logging
        **kwargs: Additional arguments passed to operation

    Returns:
        Operation result

    Raises:
        Last exception if all retries fail
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return operation(**kwargs)

        except Exception as e:
            last_error = e

            # Don't retry if not retryable or last attempt
            if not is_retryable(e) or attempt >= max_retries:
                logger.error(f"{error_message}: {e}")
                raise

            # Calculate backoff
            delay = exponential_backoff(attempt, base_delay=base_delay)

            logger.warning(
                f"{error_message} (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {delay:.2f}s: {e}"
            )

            time.sleep(delay)

    # Should never reach here
    if last_error:
        raise last_error


__all__ = [
    'exponential_backoff',
    'retry_with_backoff',
    'RetryContext',
    'retry_on_failure',
]
