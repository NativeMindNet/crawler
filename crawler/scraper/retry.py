"""Retry logic with exponential backoff."""

import asyncio
import random
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add 0-25% jitter
            delay = delay * (0.75 + random.random() * 0.25)

        return delay


async def retry_with_backoff(
    func: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    **kwargs,
) -> Any:
    """
    Execute function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: Retry configuration
        on_retry: Callback called on each retry (attempt, exception)
        **kwargs: Keyword arguments for func
    
    Returns:
        Result from func
    
    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except config.retryable_exceptions as e:
            last_exception = e

            if attempt >= config.max_retries:
                break

            delay = config.get_delay(attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s"
            )

            if on_retry:
                on_retry(attempt, e)

            await asyncio.sleep(delay)

    raise last_exception


def retry_decorator(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """Decorator for retry with backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                func, *args, config=config, on_retry=on_retry, **kwargs
            )
        return wrapper
    return decorator
