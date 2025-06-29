"""
test_immutable_guard.py

Tests for the Immutable Guard - comprehensive test suite
Tests immutable field monitoring and violation detection functionality.
"""

import pytest
import json
import tempfile
import os
from src.plugins.immutable_guard import (
    ImmutableGuard,
    check_immutable_guard,
    immutable_guard,
)
from src.exceptions import RetryException


class TestImmutableGuard:
    """Test class for immutable guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for test files
        self.temp_dir = tempfile.mkdtemp()
        self.snapshot_path = os.path.join(self.temp_dir, "test_snapshot.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_immutable_guard_first_run_creates_snapshot(self):
        """Test that first run creates snapshot and passes."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)
        result = guard.check(characters)

        assert result["passed"] is True
        assert result["snapshot_created"] is True
        assert len(result["violations"]) == 0
        assert os.path.exists(self.snapshot_path)

        # Verify snapshot content
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "MC" in snapshot
        assert snapshot["MC"]["birth"] == "2002-07-15"
        assert snapshot["MC"]["hometown"] == "서울"

    def test_immutable_guard_passes_with_no_changes(self):
        """Test that guard passes when no immutable fields change."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Second run - same data should pass
        result = guard.check(characters)

        assert result["passed"] is True
        assert result["snapshot_created"] is False
        assert len(result["violations"]) == 0

    def test_immutable_guard_passes_with_non_immutable_changes(self):
        """Test that guard passes when only non-immutable fields change."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "age": 21,
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Change non-immutable field
        characters["MC"]["age"] = 22
        characters["MC"]["name"] = "정선우 (변경됨)"

        result = guard.check(characters)

        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_immutable_guard_fails_on_birth_change(self):
        """Test that guard fails when birth (immutable field) changes."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Change immutable field
        characters["MC"]["birth"] = "2003-07-15"

        with pytest.raises(RetryException) as exc_info:
            guard.check(characters)

        exception = exc_info.value
        assert exception.guard_name == "immutable_guard"
        assert "immutable_breach" in exception.flags
        assert exception.flags["immutable_breach"]["count"] == 1
        assert len(exception.flags["immutable_breach"]["details"]) == 1

        violation = exception.flags["immutable_breach"]["details"][0]
        assert violation["character"] == "MC"
        assert violation["field"] == "birth"
        assert violation["original_value"] == "2002-07-15"
        assert violation["current_value"] == "2003-07-15"

    def test_immutable_guard_fails_on_hometown_change(self):
        """Test that guard fails when hometown (immutable field) changes."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Change immutable field
        characters["MC"]["hometown"] = "부산"

        with pytest.raises(RetryException) as exc_info:
            guard.check(characters)

        exception = exc_info.value
        assert exception.guard_name == "immutable_guard"
        assert "MC.hometown: 서울 → 부산" in str(exception)

    def test_immutable_guard_fails_on_multiple_violations(self):
        """Test that guard detects multiple immutable field violations."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            },
            "Alice": {
                "name": "Alice",
                "age": 25,
                "background": "Royal Guard",
                "immutable": ["age", "background"],
            },
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Change multiple immutable fields
        characters["MC"]["birth"] = "2003-07-15"
        characters["MC"]["hometown"] = "부산"
        characters["Alice"]["age"] = 26

        with pytest.raises(RetryException) as exc_info:
            guard.check(characters)

        exception = exc_info.value
        assert exception.guard_name == "immutable_guard"
        assert exception.flags["immutable_breach"]["count"] == 3
        assert len(exception.flags["immutable_breach"]["details"]) == 3

    def test_immutable_guard_handles_new_characters(self):
        """Test that guard handles new characters correctly."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Add new character
        characters["Alice"] = {
            "name": "Alice",
            "age": 25,
            "background": "Royal Guard",
            "immutable": ["age", "background"],
        }

        result = guard.check(characters)

        assert result["passed"] is True
        assert len(result["violations"]) == 0

        # Verify new character is in snapshot
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "Alice" in snapshot
        assert snapshot["Alice"]["age"] == 25
        assert snapshot["Alice"]["background"] == "Royal Guard"

    def test_immutable_guard_handles_characters_without_immutable_fields(self):
        """Test that guard handles characters without immutable fields."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            },
            "NPC": {
                "name": "Bob",
                "role": "shopkeeper",
                # No immutable field
            },
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)
        result = guard.check(characters)

        assert result["passed"] is True

        # Verify only MC is in snapshot
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "MC" in snapshot
        assert "NPC" not in snapshot

    def test_immutable_guard_handles_empty_characters(self):
        """Test that guard handles empty character data."""
        characters = {}

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)
        result = guard.check(characters)

        assert result["passed"] is True
        assert result["snapshot_created"] is True
        assert len(result["violations"]) == 0

    def test_immutable_guard_handles_malformed_character_data(self):
        """Test that guard handles malformed character data gracefully."""
        characters = {
            "MC": "not a dict",  # Invalid character data
            "Alice": {"name": "Alice", "age": 25, "immutable": ["age"]},
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)
        result = guard.check(characters)

        assert result["passed"] is True

        # Only Alice should be in snapshot
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "MC" not in snapshot
        assert "Alice" in snapshot

    def test_immutable_guard_handles_missing_immutable_field_values(self):
        """Test that guard handles missing immutable field values."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                # hometown is missing but listed as immutable
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)
        result = guard.check(characters)

        assert result["passed"] is True

        # Only birth should be in snapshot
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        assert "MC" in snapshot
        assert "birth" in snapshot["MC"]
        assert "hometown" not in snapshot["MC"]

    def test_check_immutable_guard_function(self):
        """Test the check_immutable_guard convenience function."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        # Create temporary snapshot for this test
        temp_snapshot = os.path.join(self.temp_dir, "func_test_snapshot.json")

        # Patch the default snapshot path temporarily
        original_init = ImmutableGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, snapshot_path=temp_snapshot)

        ImmutableGuard.__init__ = patched_init

        try:
            result = check_immutable_guard(characters)
            assert result["passed"] is True
            assert result["snapshot_created"] is True
        finally:
            # Restore original init
            ImmutableGuard.__init__ = original_init

    def test_immutable_guard_main_function_pass(self):
        """Test the main immutable_guard function when it should pass."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        # Create temporary snapshot for this test
        temp_snapshot = os.path.join(self.temp_dir, "main_test_snapshot.json")

        # Patch the default snapshot path temporarily
        original_init = ImmutableGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, snapshot_path=temp_snapshot)

        ImmutableGuard.__init__ = patched_init

        try:
            result = immutable_guard(characters)
            assert result is True
        finally:
            # Restore original init
            ImmutableGuard.__init__ = original_init

    def test_immutable_guard_main_function_fail(self):
        """Test the main immutable_guard function when it should fail."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        # Create temporary snapshot for this test
        temp_snapshot = os.path.join(self.temp_dir, "main_fail_test_snapshot.json")

        guard = ImmutableGuard(snapshot_path=temp_snapshot)

        # First run - create snapshot
        guard.check(characters)

        # Change immutable field
        characters["MC"]["birth"] = "2003-07-15"

        # Patch the default snapshot path temporarily
        original_init = ImmutableGuard.__init__

        def patched_init(self, *args, project="default", **kwargs):
            original_init(self, snapshot_path=temp_snapshot)

        ImmutableGuard.__init__ = patched_init

        try:
            with pytest.raises(RetryException) as exc_info:
                immutable_guard(characters)

            exception = exc_info.value
            assert exception.guard_name == "immutable_guard"
        finally:
            # Restore original init
            ImmutableGuard.__init__ = original_init

    def test_immutable_guard_exception_message_format(self):
        """Test that RetryException has correct message format."""
        characters = {
            "MC": {
                "name": "정선우",
                "birth": "2002-07-15",
                "hometown": "서울",
                "immutable": ["birth", "hometown"],
            }
        }

        guard = ImmutableGuard(snapshot_path=self.snapshot_path)

        # First run - create snapshot
        guard.check(characters)

        # Change immutable field
        characters["MC"]["birth"] = "2003-07-15"

        with pytest.raises(RetryException) as exc_info:
            guard.check(characters)

        exception = exc_info.value
        assert str(exception).startswith(
            "[immutable_guard] Immutable field violations:"
        )
        assert "MC.birth: 2002-07-15 → 2003-07-15" in str(exception)
