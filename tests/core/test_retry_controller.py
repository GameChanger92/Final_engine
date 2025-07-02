"""
test_retry_controller.py

Tests for the Retry Controller - comprehensive test suite.
Tests retry functionality, backoff intervals, and error handling.
"""

import os
from unittest.mock import Mock, patch

import pytest

from src.core.retry_controller import run_with_retry
from src.exceptions import RetryException


class TestRetryController:
    """Test class for retry controller functionality."""

    def test_run_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_func"

        result = run_with_retry(mock_func, "arg1", kwarg1="value1")

        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", kwarg1="value1")

    def test_run_with_retry_success_after_one_retry(self):
        """Test successful execution after 1 retry."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("First attempt failed", guard_name="test_guard"),
            "success",
        ]

        result = run_with_retry(mock_func, max_retry=2)

        assert result == "success"
        assert mock_func.call_count == 2

    def test_run_with_retry_success_after_two_retries(self):
        """Test successful execution after 2 retries (3rd attempt)."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("First attempt failed", guard_name="test_guard"),
            RetryException("Second attempt failed", guard_name="test_guard"),
            "success",
        ]

        result = run_with_retry(mock_func, max_retry=2)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_run_with_retry_all_attempts_fail(self):
        """Test that all 3 attempts fail and final exception is raised."""
        os.environ["UNIT_TEST_MODE"] = "1"
        try:
            mock_func = Mock()
            mock_func.__name__ = "test_func"
            mock_func.side_effect = [
                RetryException("First attempt failed", guard_name="test_guard"),
                RetryException("Second attempt failed", guard_name="test_guard"),
                RetryException("Third attempt failed", guard_name="test_guard"),
            ]

            with pytest.raises(RetryException) as exc_info:
                run_with_retry(mock_func, max_retry=2)

            assert mock_func.call_count == 3
            exception = exc_info.value
            # The exception messages include guard name formatting, so check that all messages are present
            exception_str = str(exception)
            assert "First attempt failed" in exception_str
            assert "Second attempt failed" in exception_str
            assert "Third attempt failed" in exception_str
            assert exception.guard_name == "test_guard"
        finally:
            if "UNIT_TEST_MODE" in os.environ:
                del os.environ["UNIT_TEST_MODE"]

    def test_run_with_retry_preserves_exception_flags(self):
        """Test that exception flags are preserved in final exception."""
        test_flags = {"test_flag": {"error": "test_error"}}
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = RetryException(
            "Test failure", flags=test_flags, guard_name="test_guard"
        )

        with pytest.raises(RetryException) as exc_info:
            run_with_retry(mock_func, max_retry=1)

        exception = exc_info.value
        assert exception.flags == test_flags
        assert exception.guard_name == "test_guard"

    @patch("time.sleep")
    def test_run_with_retry_backoff_intervals(self, mock_sleep):
        """Test that exponential backoff intervals are correct."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("First attempt failed", guard_name="test_guard"),
            RetryException("Second attempt failed", guard_name="test_guard"),
            RetryException("Third attempt failed", guard_name="test_guard"),
        ]

        with pytest.raises(RetryException):
            run_with_retry(mock_func, max_retry=2)

        # Verify sleep was called with correct intervals
        expected_calls = [0.5, 1.0]  # 0.5 * (attempt + 1) for attempts 0 and 1
        actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_calls == expected_calls
        assert mock_sleep.call_count == 2

    def test_run_with_retry_non_retry_exception_no_retry(self):
        """Test that non-RetryException errors are not retried."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = ValueError("Not a retry exception")

        with pytest.raises(ValueError) as exc_info:
            run_with_retry(mock_func, max_retry=2)

        assert mock_func.call_count == 1
        assert str(exc_info.value) == "Not a retry exception"

    def test_run_with_retry_custom_max_retry(self):
        """Test with custom max_retry value."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("Attempt 1 failed", guard_name="test_guard"),
            RetryException("Attempt 2 failed", guard_name="test_guard"),
            RetryException("Attempt 3 failed", guard_name="test_guard"),
            RetryException("Attempt 4 failed", guard_name="test_guard"),
            "success",
        ]

        result = run_with_retry(mock_func, max_retry=4)

        assert result == "success"
        assert mock_func.call_count == 5

    def test_run_with_retry_zero_max_retry(self):
        """Test with max_retry=0 (only one attempt)."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = RetryException("Only attempt failed", guard_name="test_guard")

        with pytest.raises(RetryException):
            run_with_retry(mock_func, max_retry=0)

        assert mock_func.call_count == 1

    def test_run_with_retry_function_arguments_preserved(self):
        """Test that function arguments are preserved across retries."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("First attempt failed", guard_name="test_guard"),
            "success",
        ]

        result = run_with_retry(
            mock_func, "arg1", "arg2", kwarg1="value1", kwarg2="value2", max_retry=2
        )

        assert result == "success"
        assert mock_func.call_count == 2

        # Verify all calls had the same arguments
        for call in mock_func.call_args_list:
            assert call[0] == ("arg1", "arg2")
            assert call[1] == {"kwarg1": "value1", "kwarg2": "value2"}

    @patch("src.core.retry_controller.logger")
    def test_run_with_retry_logging_success(self, mock_logger):
        """Test logging for successful execution."""
        mock_func = Mock(return_value="success")
        mock_func.__name__ = "test_function"

        run_with_retry(mock_func, max_retry=2)

        mock_logger.info.assert_called_with(
            "Retry Controller: Executing test_function (attempt 1/3)"
        )

    @patch("src.core.retry_controller.logger")
    def test_run_with_retry_logging_retries(self, mock_logger):
        """Test logging for retry attempts."""
        mock_func = Mock()
        mock_func.__name__ = "test_function"
        mock_func.side_effect = [
            RetryException("First failed", guard_name="test_guard"),
            "success",
        ]

        run_with_retry(mock_func, max_retry=2)

        # Check that retry logging occurred
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("retry 1/3" in call for call in info_calls)
        assert any("Waiting 0.5s before retry" in call for call in info_calls)

    @patch("src.core.retry_controller.logger")
    def test_run_with_retry_logging_final_failure(self, mock_logger):
        """Test logging for final failure after all retries."""
        mock_func = Mock()
        mock_func.__name__ = "test_function"
        mock_func.side_effect = RetryException("Always fails", guard_name="test_guard")

        with pytest.raises(RetryException):
            run_with_retry(mock_func, max_retry=1)

        mock_logger.error.assert_called()
        error_call = str(mock_logger.error.call_args_list[0])
        assert "failed after 2 attempts" in error_call

    def test_run_with_retry_mixed_exception_types(self):
        """Test behavior with mixed RetryException and other exceptions."""
        mock_func = Mock()
        mock_func.__name__ = "test_func"
        mock_func.side_effect = [
            RetryException("Retry this", guard_name="test_guard"),
            ValueError("Don't retry this"),
        ]

        with pytest.raises(ValueError):
            run_with_retry(mock_func, max_retry=2)

        assert mock_func.call_count == 2

    def test_run_with_retry_exception_without_guard_name(self):
        """Test RetryException without guard_name uses function name."""
        mock_func = Mock()
        mock_func.__name__ = "test_function"
        mock_func.side_effect = RetryException("No guard name")

        with pytest.raises(RetryException) as exc_info:
            run_with_retry(mock_func, max_retry=0)

        exception = exc_info.value
        assert exception.guard_name == "test_function"
