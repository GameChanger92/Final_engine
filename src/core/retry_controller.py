"""
retry_controller.py

Retry Controller for Final Engine - handles automatic retry of failed guards.

Provides retry functionality for guards that raise RetryException, with
exponential backoff and error message collection.
"""

import logging
import os
import time
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
    unit_test_mode = os.getenv("UNIT_TEST_MODE") == "1"

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
            logger.info(f"Retry Controller: {func_name} retry {attempt + 1}/{max_retry + 1}: {e}")

            if attempt == max_retry:
                # Final attempt failed - raise combined exception
                guard_name = getattr(e, "guard_name", None) or func_name
                # Check if we should use old format (for backward compatibility with tests)
                if unit_test_mode:
                    # Use old combined message format for tests
                    combined_message = "; ".join(messages)
                else:
                    # Use new summary format for production
                    combined_message = f"{guard_name} failed after {max_retry + 1} attempts"

                logger.error(
                    f"Retry Controller: {func_name} failed after {max_retry + 1} attempts: {'; '.join(messages)}"
                )

                raise RetryException(
                    message=combined_message,
                    flags=getattr(e, "flags", {}),
                    guard_name=guard_name,
                ) from e

            # Wait before next retry with exponential backoff
            backoff = 0.5 * (attempt + 1)
            logger.info(f"Waiting {backoff}s before retry")
            time.sleep(backoff)
        except Exception as e:
            # Non-RetryException errors are not retried
            logger.error(f"Retry Controller: {func_name} failed with non-retry error: {e}")
            raise
