"""
test_date_guard.py

Tests for the Date Guard - comprehensive test suite
Tests date progression monitoring and backstep detection functionality.
"""

import json
import os
import tempfile

import pytest

from src.exceptions import RetryException
from src.plugins.date_guard import (
    DateGuard,
    check_date_guard,
    date_guard,
)


class TestDateGuard:
    """Test class for date guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for test files
        self.temp_dir = tempfile.mkdtemp()
        self.date_log_path = os.path.join(self.temp_dir, "test_dates.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_date_guard_first_run_creates_log(self):
        """Test that first run creates date log and passes."""
        context = {"date": "2024-01-01"}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["date_log_created"] is True
        assert result["current_date"] == "2024-01-01"
        assert result["current_episode"] == 1
        assert os.path.exists(self.date_log_path)

        # Verify log content
        with open(self.date_log_path, encoding="utf-8") as f:
            log = json.load(f)

        assert "1" in log
        assert log["1"] == "2024-01-01"

    def test_date_guard_passes_with_forward_progression(self):
        """Test that guard passes when dates progress forward."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-01-01"}
        guard.check(context1, 1)

        # Episode 2 - later date should pass
        context2 = {"date": "2024-01-02"}
        result = guard.check(context2, 2)

        assert result["passed"] is True
        assert result["current_date"] == "2024-01-02"
        assert result["previous_date"] == "2024-01-01"
        assert result["previous_episode"] == 1

    def test_date_guard_passes_with_same_date(self):
        """Test that guard passes when dates are the same."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-01-01"}
        guard.check(context1, 1)

        # Episode 2 - same date should pass
        context2 = {"date": "2024-01-01"}
        result = guard.check(context2, 2)

        assert result["passed"] is True

    def test_date_guard_fails_on_backward_date(self):
        """Test that guard fails when date goes backward."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-01-05"}
        guard.check(context1, 1)

        # Episode 2 - earlier date should fail
        context2 = {"date": "2024-01-03"}

        with pytest.raises(RetryException) as exc_info:
            guard.check(context2, 2)

        exception = exc_info.value
        assert exception.guard_name == "date_guard"
        assert "date_backstep" in exception.flags

        backstep = exception.flags["date_backstep"]
        assert backstep["current_date"] == "2024-01-03"
        assert backstep["previous_date"] == "2024-01-05"
        assert backstep["current_episode"] == 2
        assert backstep["previous_episode"] == 1
        assert backstep["days_backward"] == 2

    def test_date_guard_handles_meta_date(self):
        """Test that guard can extract date from meta field."""
        context = {"meta": {"date": "2024-01-01", "author": "test"}}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["current_date"] == "2024-01-01"

    def test_date_guard_handles_episode_date_field(self):
        """Test that guard can extract date from episode_date field."""
        context = {"episode_date": "2024-01-01"}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["current_date"] == "2024-01-01"

    def test_date_guard_passes_with_no_date(self):
        """Test that guard passes when no date is found in context."""
        context = {"title": "Episode without date"}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["current_date"] is None

    def test_date_guard_handles_alternative_date_format(self):
        """Test that guard handles alternative date formats."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1 with slash format
        context1 = {"date": "2024/01/01"}
        guard.check(context1, 1)

        # Episode 2 - later date with standard format
        context2 = {"date": "2024-01-02"}
        result = guard.check(context2, 2)

        assert result["passed"] is True

    def test_date_guard_handles_invalid_date_format(self):
        """Test that guard handles invalid date formats gracefully."""
        context = {"date": "invalid-date"}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True  # Invalid dates are ignored
        assert result["current_date"] == "invalid-date"

    def test_date_guard_handles_multiple_episodes_with_gap(self):
        """Test that guard handles non-sequential episode numbers."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-01-01"}
        guard.check(context1, 1)

        # Episode 5 (skipping 2, 3, 4)
        context5 = {"date": "2024-01-05"}
        result = guard.check(context5, 5)

        assert result["passed"] is True
        assert result["previous_episode"] == 1

        # Episode 3 (between 1 and 5)
        context3 = {"date": "2024-01-03"}
        result = guard.check(context3, 3)

        assert result["passed"] is True
        assert result["previous_episode"] == 1  # Most recent previous episode

    def test_date_guard_fails_on_large_backward_jump(self):
        """Test that guard fails on large backward date jumps."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-12-31"}
        guard.check(context1, 1)

        # Episode 2 - much earlier date
        context2 = {"date": "2024-01-01"}

        with pytest.raises(RetryException) as exc_info:
            guard.check(context2, 2)

        exception = exc_info.value
        backstep = exception.flags["date_backstep"]
        assert backstep["days_backward"] == 365  # Approximate days in year

    def test_date_guard_handles_existing_log_file(self):
        """Test that guard handles existing log files correctly."""
        # Create pre-existing log
        existing_log = {"1": "2024-01-01", "2": "2024-01-02"}
        with open(self.date_log_path, "w", encoding="utf-8") as f:
            json.dump(existing_log, f)

        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 3 should use episode 2 as reference
        context3 = {"date": "2024-01-01"}  # Earlier than episode 2

        with pytest.raises(RetryException) as exc_info:
            guard.check(context3, 3)

        exception = exc_info.value
        backstep = exception.flags["date_backstep"]
        assert backstep["previous_episode"] == 2
        assert backstep["previous_date"] == "2024-01-02"

    def test_date_guard_handles_corrupted_log_file(self):
        """Test that guard handles corrupted log files gracefully."""
        # Create corrupted log file
        with open(self.date_log_path, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        context = {"date": "2024-01-01"}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["date_log_created"] is True

    def test_date_guard_handles_empty_context(self):
        """Test that guard handles empty context gracefully."""
        context = {}
        episode_num = 1

        guard = DateGuard(date_log_path=self.date_log_path)
        result = guard.check(context, episode_num)

        assert result["passed"] is True
        assert result["current_date"] is None

    def test_check_date_guard_function(self):
        """Test the check_date_guard convenience function."""
        context = {"date": "2024-01-01"}
        episode_num = 1

        # Create temporary log for this test
        temp_log = os.path.join(self.temp_dir, "func_test_dates.json")

        # Patch the default log path temporarily
        original_init = DateGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, date_log_path=temp_log)

        DateGuard.__init__ = patched_init

        try:
            result = check_date_guard(context, episode_num)
            assert result["passed"] is True
            assert result["date_log_created"] is True
        finally:
            # Restore original init
            DateGuard.__init__ = original_init

    def test_date_guard_main_function_pass(self):
        """Test the main date_guard function when it should pass."""
        context = {"date": "2024-01-01"}
        episode_num = 1

        # Create temporary log for this test
        temp_log = os.path.join(self.temp_dir, "main_test_dates.json")

        # Patch the default log path temporarily
        original_init = DateGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, date_log_path=temp_log)

        DateGuard.__init__ = patched_init

        try:
            result = date_guard(context, episode_num)
            assert result is True
        finally:
            # Restore original init
            DateGuard.__init__ = original_init

    def test_date_guard_main_function_fail(self):
        """Test the main date_guard function when it should fail."""
        # Create temporary log for this test
        temp_log = os.path.join(self.temp_dir, "main_fail_test_dates.json")

        guard = DateGuard(date_log_path=temp_log)

        # Episode 1
        context1 = {"date": "2024-01-05"}
        guard.check(context1, 1)

        # Episode 2 - earlier date
        context2 = {"date": "2024-01-03"}

        # Patch the default log path temporarily
        original_init = DateGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, date_log_path=temp_log)

        DateGuard.__init__ = patched_init

        try:
            with pytest.raises(RetryException) as exc_info:
                date_guard(context2, 2)

            exception = exc_info.value
            assert exception.guard_name == "date_guard"
        finally:
            # Restore original init
            DateGuard.__init__ = original_init

    def test_date_guard_exception_message_format(self):
        """Test that RetryException has correct message format."""
        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 1
        context1 = {"date": "2024-01-05"}
        guard.check(context1, 1)

        # Episode 2 - earlier date
        context2 = {"date": "2024-01-03"}

        with pytest.raises(RetryException) as exc_info:
            guard.check(context2, 2)

        exception = exc_info.value
        assert str(exception).startswith("[date_guard] Date backstep:")
        assert "Episode 2 (2024-01-03) goes back 2 days from Episode 1 (2024-01-05)" in str(
            exception
        )

    def test_date_guard_handles_string_episode_numbers_in_log(self):
        """Test that guard handles string episode numbers in existing log."""
        # Create log with string keys (normal JSON behavior)
        existing_log = {"1": "2024-01-01", "3": "2024-01-03"}
        with open(self.date_log_path, "w", encoding="utf-8") as f:
            json.dump(existing_log, f)

        guard = DateGuard(date_log_path=self.date_log_path)

        # Episode 2 should use episode 1 as reference (most recent previous)
        context2 = {"date": "2024-01-02"}
        result = guard.check(context2, 2)

        assert result["passed"] is True
        assert result["previous_episode"] == 1
        assert result["previous_date"] == "2024-01-01"
