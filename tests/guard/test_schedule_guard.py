"""
test_schedule_guard.py

Tests for the Schedule Guard - comprehensive test suite.
Tests foreshadow schedule compliance checking and payoff update functionality.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.exceptions import RetryException
from src.plugins.schedule_guard import (
    ScheduleGuard,
    check_schedule_guard,
    schedule_guard,
)


class TestScheduleGuard:
    """Test class for schedule guard functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "foreshadow.json")

        # Patch the file path to use our test file
        self.patcher = patch(
            "src.plugins.foreshadow_scheduler._get_foreshadow_file_path",
            return_value=self.test_file,
        )
        self.patcher.start()

    def teardown_method(self):
        """Clean up after each test."""
        # Stop the patcher
        self.patcher.stop()

        # Clean up test file
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def _create_test_foreshadows(self, foreshadows_data: list):
        """Helper to create test foreshadow data."""
        data = {"foreshadows": foreshadows_data}
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def test_schedule_guard_passes_before_due_date(self):
        """Test that guard passes when current episode is before due dates."""
        # Create foreshadows with future due dates
        foreshadows = [
            {
                "id": "f001",
                "hint": "미래 복선 1",
                "introduced": 5,
                "due": 20,
                "payoff": None,
            },
            {
                "id": "f002",
                "hint": "미래 복선 2",
                "introduced": 8,
                "due": 25,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        current_episode = 15  # Before both due dates

        # Should pass without raising exception
        result = guard.check(current_episode)

        assert result["passed"] is True
        assert result["current_episode"] == 15
        assert len(result["overdue_foreshadows"]) == 0
        assert result["flags"] == {}

    def test_schedule_guard_passes_with_resolved_foreshadows(self):
        """Test that guard passes when foreshadows are already resolved."""
        # Create foreshadows that are resolved
        foreshadows = [
            {
                "id": "f001",
                "hint": "해결된 복선",
                "introduced": 5,
                "due": 15,
                "payoff": 12,  # Already resolved
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        current_episode = 20  # Past due date, but already resolved

        # Should pass because foreshadow is resolved
        result = guard.check(current_episode)

        assert result["passed"] is True
        assert len(result["overdue_foreshadows"]) == 0

    def test_schedule_guard_fails_on_due_date_with_null_payoff(self):
        """Test that guard fails when due date is reached and payoff is null."""
        # Create foreshadow with due date equal to current episode
        foreshadows = [
            {
                "id": "f001",
                "hint": "마감일 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        current_episode = 16  # One episode past due

        with pytest.raises(RetryException) as exc_info:
            guard.check(current_episode)

        exception = exc_info.value
        assert exception.guard_name == "schedule_guard"
        assert "overdue_foreshadows" in exception.flags
        assert exception.flags["overdue_foreshadows"]["count"] == 1
        assert len(exception.flags["overdue_foreshadows"]["details"]) == 1

        detail = exception.flags["overdue_foreshadows"]["details"][0]
        assert detail["id"] == "f001"
        assert detail["episodes_overdue"] == 1

    def test_schedule_guard_fails_past_due_date_with_null_payoff(self):
        """Test that guard fails when episode is past due date and payoff is null."""
        # Create foreshadow with due date in the past
        foreshadows = [
            {
                "id": "f001",
                "hint": "과거 마감 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        current_episode = 25  # 10 episodes past due

        with pytest.raises(RetryException) as exc_info:
            guard.check(current_episode)

        exception = exc_info.value
        assert exception.guard_name == "schedule_guard"
        assert "overdue_foreshadows" in exception.flags

        detail = exception.flags["overdue_foreshadows"]["details"][0]
        assert detail["episodes_overdue"] == 10

    def test_schedule_guard_multiple_overdue_foreshadows(self):
        """Test handling of multiple overdue foreshadows."""
        # Create multiple overdue foreshadows
        foreshadows = [
            {
                "id": "f001",
                "hint": "첫 번째 과거 복선",
                "introduced": 3,
                "due": 10,
                "payoff": None,
            },
            {
                "id": "f002",
                "hint": "두 번째 과거 복선",
                "introduced": 5,
                "due": 12,
                "payoff": None,
            },
            {
                "id": "f003",
                "hint": "미래 복선",  # This one should not be flagged
                "introduced": 15,
                "due": 25,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        current_episode = 20

        with pytest.raises(RetryException) as exc_info:
            guard.check(current_episode)

        exception = exc_info.value
        assert exception.flags["overdue_foreshadows"]["count"] == 2
        assert len(exception.flags["overdue_foreshadows"]["details"]) == 2

        # Check that the overdue ones are correct
        overdue_ids = [d["id"] for d in exception.flags["overdue_foreshadows"]["details"]]
        assert "f001" in overdue_ids
        assert "f002" in overdue_ids
        assert "f003" not in overdue_ids

    def test_update_payoff_success(self):
        """Test successful payoff update."""
        # Create unresolved foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "업데이트할 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        result = guard.update_payoff("f001", 12)

        assert result is True

        # Verify the file was updated
        with open(self.test_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["foreshadows"][0]["payoff"] == 12

    def test_update_payoff_nonexistent_id(self):
        """Test payoff update with non-existent foreshadow ID."""
        # Create foreshadow data
        foreshadows = [
            {
                "id": "f001",
                "hint": "존재하는 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        result = guard.update_payoff("f999", 12)  # Non-existent ID

        assert result is False

    def test_update_payoff_already_resolved(self):
        """Test payoff update on already resolved foreshadow."""
        # Create already resolved foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "이미 해결된 복선",
                "introduced": 5,
                "due": 15,
                "payoff": 10,  # Already resolved
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()
        result = guard.update_payoff("f001", 12)  # Try to update again

        assert result is False

        # Verify payoff didn't change
        with open(self.test_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["foreshadows"][0]["payoff"] == 10  # Original value

    def test_schedule_guard_empty_file(self):
        """Test schedule guard with empty foreshadows file."""
        # Create empty foreshadows structure
        self._create_test_foreshadows([])

        guard = ScheduleGuard()
        result = guard.check(20)

        assert result["passed"] is True
        assert len(result["overdue_foreshadows"]) == 0

    def test_schedule_guard_missing_file(self):
        """Test schedule guard when foreshadow file doesn't exist."""
        # Don't create the file at all
        guard = ScheduleGuard()
        result = guard.check(20)

        assert result["passed"] is True
        assert len(result["overdue_foreshadows"]) == 0

    def test_check_schedule_guard_function(self):
        """Test the standalone check_schedule_guard function."""
        # Create overdue foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "함수 테스트 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        with pytest.raises(RetryException) as exc_info:
            check_schedule_guard(20)

        exception = exc_info.value
        assert exception.guard_name == "schedule_guard"

    def test_schedule_guard_main_function_pass(self):
        """Test the main schedule_guard function when checks pass."""
        # Create future due date foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "미래 복선",
                "introduced": 5,
                "due": 25,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        result = schedule_guard(15)
        assert result is True

    def test_schedule_guard_main_function_fail(self):
        """Test the main schedule_guard function when checks fail."""
        # Create overdue foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "과거 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        with pytest.raises(RetryException):
            schedule_guard(20)

    def test_schedule_guard_results_structure(self):
        """Test that schedule guard returns proper results structure."""
        # Create mixed foreshadows
        foreshadows = [
            {
                "id": "f001",
                "hint": "과거 복선",
                "introduced": 3,
                "due": 10,
                "payoff": None,
            },
            {
                "id": "f002",
                "hint": "미래 복선",
                "introduced": 15,
                "due": 25,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        guard = ScheduleGuard()

        try:
            guard.check(20)
        except RetryException:
            pass  # Expected

        # Test with no overdue foreshadows
        result = guard.check(5)  # Before any due dates

        assert "current_episode" in result
        assert "overdue_foreshadows" in result
        assert "flags" in result
        assert "passed" in result
        assert result["passed"] is True
        assert isinstance(result["overdue_foreshadows"], list)
        assert isinstance(result["flags"], dict)
        assert result["current_episode"] == 5

    def test_schedule_guard_exception_message(self):
        """Test that RetryException has correct message format."""
        # Create overdue foreshadow
        foreshadows = [
            {
                "id": "f001",
                "hint": "메시지 테스트 복선",
                "introduced": 5,
                "due": 15,
                "payoff": None,
            },
        ]
        self._create_test_foreshadows(foreshadows)

        with pytest.raises(RetryException) as exc_info:
            schedule_guard(20)

        exception = exc_info.value
        assert str(exception).startswith("[schedule_guard] Foreshadow schedule violations")
        assert "1 foreshadow(s) past due episode" in str(exception)
