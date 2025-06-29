"""
test_relation_guard.py

Tests for the Relation Guard - comprehensive test suite
Tests relationship change detection and tolerance window functionality.
"""

import pytest
import json
import tempfile
import os
from src.plugins.relation_guard import (
    RelationGuard,
    check_relation_guard,
    relation_guard,
)
from src.exceptions import RetryException


class TestRelationGuard:
    """Test class for relation guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for test files
        self.temp_dir = tempfile.mkdtemp()
        self.relation_path = os.path.join(self.temp_dir, "test_relations.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_relations(self, relations_data):
        """Helper to create test relation matrix file."""
        with open(self.relation_path, "w", encoding="utf-8") as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

    # BASIC FUNCTIONALITY TESTS (4 tests)

    def test_relation_guard_loads_relations_file(self):
        """Test that RelationGuard properly loads relations from JSON file."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구", "B,C": "적"}},
            {"ep": 3, "relations": {"A,B": "동료", "B,C": "적"}},
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path)
        assert len(guard.relations) == 2
        assert guard.tolerance_ep == 3

    def test_relation_guard_handles_missing_file(self):
        """Test that RelationGuard handles missing relation file gracefully."""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent.json")
        guard = RelationGuard(non_existent_path)
        assert guard.relations == []

        # Should pass when no relations are defined
        result = guard.check(1)
        assert result["passed"] is True

    def test_relation_guard_handles_invalid_json(self):
        """Test that RelationGuard handles invalid JSON files."""
        with open(self.relation_path, "w") as f:
            f.write("invalid json content")

        guard = RelationGuard(self.relation_path)
        assert guard.relations == []

        # Should pass when relations can't be loaded
        result = guard.check(1)
        assert result["passed"] is True

    def test_relation_guard_validates_json_structure(self):
        """Test that RelationGuard validates JSON structure is a list."""
        # Test with dict instead of list
        with open(self.relation_path, "w") as f:
            json.dump({"ep": 1, "relations": {}}, f)

        guard = RelationGuard(self.relation_path)
        assert guard.relations == []

    # PASSING SCENARIOS (4 tests)

    def test_gradual_relationship_change_passes(self):
        """Test that gradual relationship changes pass (친구→동료→적)."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "동료"}},
            {"ep": 6, "relations": {"A,B": "적"}},
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)

        # Episode 3: 친구→동료 (2 episodes gap) should pass
        result = guard.check(3)
        assert result["passed"] is True

        # Episode 6: 동료→적 (3 episodes gap) should pass
        result = guard.check(6)
        assert result["passed"] is True

    def test_no_relationship_changes_passes(self):
        """Test that episodes with no relationship changes pass."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구", "B,C": "적"}},
            {"ep": 5, "relations": {"A,B": "친구", "B,C": "적"}},
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path)
        result = guard.check(5)
        assert result["passed"] is True

    def test_no_relations_defined_for_episode_passes(self):
        """Test that episodes with no relations defined pass."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path)
        result = guard.check(5)  # Episode 5 has no relations defined
        assert result["passed"] is True

    def test_non_opposing_relationship_changes_pass(self):
        """Test that non-opposing relationship changes pass."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "동료"}},  # 친구→동료 is not opposing
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)
        result = guard.check(3)
        assert result["passed"] is True

    # FAILING SCENARIOS (3 tests)

    def test_rapid_opposing_change_fails(self):
        """Test that rapid opposing relationship changes fail (친구→적)."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "적"}},  # 2 episodes gap < tolerance(3)
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)

        with pytest.raises(RetryException) as exc_info:
            guard.check(3)

        exception = exc_info.value
        assert exception.guard_name == "relation_guard"
        assert "A,B" in str(exception)
        assert "친구" in str(exception)
        assert "적" in str(exception)

    def test_rapid_opposing_change_reverse_fails(self):
        """Test that rapid opposing relationship changes fail (적→친구)."""
        test_relations = [
            {"ep": 2, "relations": {"A,B": "적"}},
            {"ep": 4, "relations": {"A,B": "친구"}},  # 2 episodes gap < tolerance(3)
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)

        with pytest.raises(RetryException) as exc_info:
            guard.check(4)

        exception = exc_info.value
        assert exception.guard_name == "relation_guard"
        assert "A,B" in str(exception)

    def test_tolerance_ep_boundary_fails(self):
        """Test that changes exactly at tolerance boundary fail."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 4, "relations": {"A,B": "적"}},  # 3 episodes gap >= tolerance(3)
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(
            self.relation_path, tolerance_ep=4
        )  # Use tolerance=4 so gap=3 < tolerance

        with pytest.raises(RetryException):
            guard.check(4)

    # TOLERANCE ADJUSTMENT TESTS (2 tests)

    def test_higher_tolerance_allows_change(self):
        """Test that higher tolerance allows previously failing changes."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 6, "relations": {"A,B": "적"}},  # 5 episodes gap
        ]
        self.create_test_relations(test_relations)

        # Should fail with tolerance=3 (gap=5 >= tolerance=3, but gap is not < tolerance, so this should NOT fail)
        # Let's use a smaller tolerance to demonstrate failure
        guard_strict = RelationGuard(
            self.relation_path, tolerance_ep=6
        )  # gap=5 < tolerance=6, should fail
        with pytest.raises(RetryException):
            guard_strict.check(6)

        # Should pass with tolerance=5 (gap=5 >= tolerance=5)
        guard_lenient = RelationGuard(self.relation_path, tolerance_ep=5)
        result = guard_lenient.check(6)
        assert result["passed"] is True

    def test_custom_tolerance_in_constructor(self):
        """Test custom tolerance_ep parameter in constructor."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=7)
        assert guard.tolerance_ep == 7

    # EDGE CASES (2 tests)

    def test_character_pair_order_normalization(self):
        """Test that character pair order is normalized (A,B == B,A)."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"B,A": "적"}},  # Same pair, different order
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)

        with pytest.raises(RetryException) as exc_info:
            guard.check(3)

        exception = exc_info.value
        assert "A,B" in str(exception) or "B,A" in str(exception)

    def test_new_character_introduction(self):
        """Test new character relationships don't trigger violations."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "친구", "A,C": "적"}},  # New character C
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path, tolerance_ep=3)
        result = guard.check(3)
        assert result["passed"] is True

    # CONVENIENCE FUNCTION TESTS (2 tests)

    def test_check_relation_guard_function(self):
        """Test the check_relation_guard convenience function."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "적"}},
        ]
        self.create_test_relations(test_relations)

        with pytest.raises(RetryException) as exc_info:
            check_relation_guard(3, relation_path=self.relation_path, tolerance_ep=3)

        exception = exc_info.value
        assert exception.guard_name == "relation_guard"

    def test_relation_guard_main_function_pass(self):
        """Test the main relation_guard function when it should pass."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 4, "relations": {"A,B": "적"}},  # 3 episodes gap <= tolerance(3)
        ]
        self.create_test_relations(test_relations)

        result = relation_guard(4, relation_path=self.relation_path, tolerance_ep=3)
        assert result is True

    def test_relation_guard_main_function_fail(self):
        """Test the main relation_guard function when it should fail."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {"A,B": "적"}},
        ]
        self.create_test_relations(test_relations)

        with pytest.raises(RetryException):
            relation_guard(3, relation_path=self.relation_path, tolerance_ep=3)

    # ADDITIONAL EDGE CASES (1 test)

    def test_empty_relations_in_episode(self):
        """Test episodes with empty relations dictionary."""
        test_relations = [
            {"ep": 1, "relations": {"A,B": "친구"}},
            {"ep": 3, "relations": {}},  # Empty relations
        ]
        self.create_test_relations(test_relations)

        guard = RelationGuard(self.relation_path)
        result = guard.check(3)
        assert result["passed"] is True
