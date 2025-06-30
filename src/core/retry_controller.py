"""
retry_controller.py

Retry Controller for Final Engine - handles automatic retry of failed guards.

Provides retry functionality for guards that raise RetryException, with
exponential backoff and error message collection.
"""

import os
import time
import logging
from typing import Any
from src.exceptions import RetryException

logger = logging.getLogger(__name__)


def run_with_retry(func, *args, max_retry=2, **kwargs) -> Any:
    """
    Execute a function with automatic retry on RetryException.

    Retries the function up to max_retry times (total max_retry + 1 attempts)
    when it raises RetryException. Implements exponential backoff between retries.

    Parameters
    ----------
    func : callable
        Function to execute with retry logic
    *args : tuple
        Positional arguments to pass to func
    max_retry : int, optional
        Maximum number of retries (default: 2, meaning total 3 attempts)
    **kwargs : dict
        Keyword arguments to pass to func

    Returns
    -------
    Any
        Return value from successful function execution

    Raises
    ------
    RetryException
        Final exception with combined error messages if all attempts fail
    Exception
        Non-RetryException errors are propagated immediately without retry

    Examples
    --------
    >>> def guard_function(text):
    ...     # Some guard logic that might raise RetryException
    ...     pass
    >>> result = run_with_retry(guard_function, "some text", max_retry=2)
    """
    fast_mode = os.getenv("FAST_MODE") == "1" or os.getenv("UNIT_TEST_MODE") == "1"
    
    messages = []

    func_name = getattr(func, "__name__", str(func))

    for attempt in range(max_retry + 1):
        try:
            logger.info(
                f"Retry Controller: Executing {func_name} (attempt {attempt + 1}/{max_retry + 1})"
            )
            return func(*args, **kwargs)
        except RetryException as e:
            messages.append(str(e))
            logger.info(
                f"Retry Controller: {func_name} retry {attempt + 1}/{max_retry + 1}: {e}"
            )

            if attempt == max_retry:
                # Final attempt failed - raise combined exception
                combined_message = "; ".join(messages)
                logger.error(
                    f"Retry Controller: {func_name} failed after {max_retry + 1} attempts: {combined_message}"
                )
                # Use guard_name from exception if available, otherwise use function name
                guard_name = getattr(e, "guard_name", None) or func_name
                raise RetryException(
                    message=combined_message,
                    flags=getattr(e, "flags", {}),
                    guard_name=guard_name,
                )

            # Wait before next retry with exponential backoff
            # Use shorter delays in fast mode
            if fast_mode:
                sleep_time = 0.01  # Very short delay for tests
            else:
                sleep_time = 0.5 * (attempt + 1)
            logger.info(f"Retry Controller: Waiting {sleep_time}s before retry...")
            time.sleep(sleep_time)
        except Exception as e:
            # Non-RetryException errors are not retried
            logger.error(
                f"Retry Controller: {func_name} failed with non-retry error: {e}"
            )
            raise
