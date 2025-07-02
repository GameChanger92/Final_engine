"""
test_anchor_guard.py

Tests for the Anchor Guard - comprehensive test suite
Tests anchor event validation and episode range checking functionality.
"""

import json
import os
import tempfile

import pytest

from src.exceptions import RetryException
from src.plugins.anchor_guard import (
    AnchorGuard,
    anchor_guard,
    check_anchor_guard,
)


class TestAnchorGuard:
    """Test class for anchor guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directories for test files
        self.temp_dir = tempfile.mkdtemp()
        self.anchors_path = os.path.join(self.temp_dir, "test_anchors.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_anchors(self, anchors_data):
        """Helper to create test anchors file."""
        with open(self.anchors_path, "w", encoding="utf-8") as f:
            json.dump(anchors_data, f, ensure_ascii=False, indent=2)

    def test_anchor_guard_loads_anchors_file(self):
        """Test that AnchorGuard properly loads anchors from JSON file."""
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 첫 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "첫 번째 시련", "anchor_ep": 5},
        ]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        assert len(guard.anchors) == 2
        assert guard.anchors[0]["id"] == "ANCHOR_01"
        assert guard.anchors[1]["goal"] == "첫 번째 시련"

    def test_anchor_guard_handles_missing_file(self):
        """Test that AnchorGuard handles missing anchors file gracefully."""
        non_existent_path = os.path.join(self.temp_dir, "missing.json")
        guard = AnchorGuard(non_existent_path)
        assert guard.anchors == []

    def test_anchor_guard_handles_invalid_json(self):
        """Test that AnchorGuard handles invalid JSON files."""
        with open(self.anchors_path, "w") as f:
            f.write("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            AnchorGuard(self.anchors_path)

    def test_anchor_guard_validates_json_structure(self):
        """Test that AnchorGuard validates JSON structure is a list."""
        # Test with object instead of list
        with open(self.anchors_path, "w") as f:
            json.dump({"not": "a list"}, f)

        with pytest.raises(ValueError, match="anchors.json must contain a list"):
            AnchorGuard(self.anchors_path)

    def test_episode_range_calculation(self):
        """Test episode range calculation (±1)."""
        guard = AnchorGuard(self.anchors_path)

        # Test exact match
        assert guard._is_episode_in_range(5, 5) is True

        # Test ±1 range
        assert guard._is_episode_in_range(4, 5) is True
        assert guard._is_episode_in_range(6, 5) is True

        # Test outside range
        assert guard._is_episode_in_range(3, 5) is False
        assert guard._is_episode_in_range(7, 5) is False

        # Test edge cases
        assert guard._is_episode_in_range(1, 2) is True
        assert guard._is_episode_in_range(1, 1) is True
        assert guard._is_episode_in_range(2, 1) is True

    def test_keyword_extraction_from_goal(self):
        """Test keyword extraction from anchor goals."""
        guard = AnchorGuard(self.anchors_path)

        # Test Korean text
        keywords = guard._extract_keywords_from_goal("주인공이 첫 번째 조력자를 만난다")
        assert "주인공" in keywords
        assert "조력자" in keywords
        assert "만난" in keywords  # "다" suffix removed

        # Test with stop words
        keywords = guard._extract_keywords_from_goal("주인공의 등장")
        assert "주인공" in keywords
        assert "등장" in keywords
        assert "의" not in keywords  # Stop word should be filtered

        # Test English text
        keywords = guard._extract_keywords_from_goal("Hero meets first ally")
        assert "Hero" in keywords
        assert "meets" in keywords
        assert "ally" in keywords

    def test_keyword_search_in_content(self):
        """Test keyword search functionality."""
        guard = AnchorGuard(self.anchors_path)

        content = "이 에피소드에서 주인공이 처음으로 등장합니다. 그의 이름은 김현우입니다."

        # Test successful search
        assert guard._search_keywords_in_content(content, ["주인공", "등장"]) is True
        assert guard._search_keywords_in_content(content, ["김현우"]) is True

        # Test failed search
        assert guard._search_keywords_in_content(content, ["조력자", "시련"]) is False

        # Test case insensitive search
        assert guard._search_keywords_in_content(content, ["주인공"]) is True
        assert guard._search_keywords_in_content(content, ["주인공".upper()]) is True

        # Test empty content
        assert guard._search_keywords_in_content("", ["주인공"]) is False

    def test_anchor_guard_pass_when_anchor_found(self):
        """Test that anchor guard passes when anchor event is found in episode."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "이번 에피소드에서 주인공이 처음으로 등장합니다."

        result = guard.check(episode_content, 1)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 1
        assert len(result["missing_anchors"]) == 0
        assert result["anchors_checked"][0]["found"] is True

    def test_anchor_guard_fail_when_anchor_missing(self):
        """Test that anchor guard fails when anchor event is missing."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "이번 에피소드는 배경 설명만 있습니다."

        with pytest.raises(RetryException) as exc_info:
            guard.check(episode_content, 1)

        assert "anchor_guard" in str(exc_info.value)
        assert "주인공 등장" in str(exc_info.value)
        assert exc_info.value.guard_name == "anchor_guard"
        assert "anchor_compliance" in exc_info.value.flags

    def test_anchor_guard_checks_episode_range(self):
        """Test that anchor guard only checks anchors in episode range."""
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "첫 시련", "anchor_ep": 5},
        ]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "이번 에피소드에서 주인공이 등장합니다."

        # Episode 1 - should check ANCHOR_01 but not ANCHOR_02
        result = guard.check(episode_content, 1)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 1
        assert result["anchors_checked"][0]["id"] == "ANCHOR_01"

        # Episode 3 - should not check any anchors (out of range)
        result = guard.check(episode_content, 3)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 0

    def test_anchor_guard_checks_adjacent_episodes(self):
        """Test that anchor guard checks episodes within ±1 range."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 5}]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "이번 에피소드에서 주인공이 등장합니다."

        # Test episodes 4, 5, 6 (all should check the anchor)
        for ep in [4, 5, 6]:
            result = guard.check(episode_content, ep)
            assert result["passed"] is True
            assert len(result["anchors_checked"]) == 1

        # Test episodes 3, 7 (should not check the anchor)
        for ep in [3, 7]:
            result = guard.check(episode_content, ep)
            assert result["passed"] is True
            assert len(result["anchors_checked"]) == 0

    def test_anchor_guard_handles_multiple_anchors(self):
        """Test anchor guard with multiple anchors in same episode range."""
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "히로인 만남", "anchor_ep": 1},
        ]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)

        # Content with both anchors
        content_both = "주인공이 등장하고 히로인과 만남이 이루어집니다."
        result = guard.check(content_both, 1)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 2
        assert len(result["missing_anchors"]) == 0

        # Content with only one anchor
        content_one = "주인공만 등장합니다. 다른 캐릭터는 없습니다."
        with pytest.raises(RetryException) as exc_info:
            guard.check(content_one, 1)

        assert len(exc_info.value.flags["anchor_compliance"]["missing_anchors"]) == 1

    def test_anchor_guard_handles_empty_content(self):
        """Test anchor guard with empty episode content."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)

        with pytest.raises(RetryException):
            guard.check("", 1)

    def test_anchor_guard_handles_malformed_anchor_data(self):
        """Test anchor guard with malformed anchor data."""
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 등장"},  # Missing anchor_ep
            {"id": "ANCHOR_02", "anchor_ep": 1},  # Missing goal
            {"id": "ANCHOR_03", "goal": "정상 앵커", "anchor_ep": 2},
        ]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "정상 앵커가 있는 에피소드입니다."

        # Should only check the properly formed anchor
        result = guard.check(episode_content, 2)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 1
        assert result["anchors_checked"][0]["id"] == "ANCHOR_03"

    def test_check_anchor_guard_function(self):
        """Test the standalone check_anchor_guard function."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        # Temporarily replace the default path
        import src.plugins.anchor_guard as anchor_module

        original_guard_class = anchor_module.AnchorGuard

        class TestAnchorGuard(original_guard_class):
            def __init__(self, *args, project="default", **kwargs):
                anchors_path = args[0] if args else "data/anchors.json"
                super().__init__(
                    self.test_path if hasattr(self, "test_path") else anchors_path,
                    project=project,
                )

        TestAnchorGuard.test_path = self.anchors_path
        anchor_module.AnchorGuard = TestAnchorGuard

        try:
            episode_content = "주인공이 등장하는 에피소드입니다."
            result = check_anchor_guard(episode_content, 1)
            assert result["passed"] is True
        finally:
            # Restore original class
            anchor_module.AnchorGuard = original_guard_class

    def test_anchor_guard_main_function_pass(self):
        """Test the main anchor_guard function when it should pass."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        # Temporarily replace the default path
        import src.plugins.anchor_guard as anchor_module

        original_guard_class = anchor_module.AnchorGuard

        class TestAnchorGuard(original_guard_class):
            def __init__(self, *args, project="default", **kwargs):
                anchors_path = args[0] if args else "data/anchors.json"
                super().__init__(
                    self.test_path if hasattr(self, "test_path") else anchors_path,
                    project=project,
                )

        TestAnchorGuard.test_path = self.anchors_path
        anchor_module.AnchorGuard = TestAnchorGuard

        try:
            episode_content = "주인공이 등장하는 에피소드입니다."
            # Should not raise an exception
            anchor_guard(episode_content, 1)
        finally:
            # Restore original class
            anchor_module.AnchorGuard = original_guard_class

    def test_anchor_guard_main_function_fail(self):
        """Test the main anchor_guard function when it should fail."""
        test_anchors = [{"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1}]
        self.create_test_anchors(test_anchors)

        # Temporarily replace the default path
        import src.plugins.anchor_guard as anchor_module

        original_guard_class = anchor_module.AnchorGuard

        class TestAnchorGuard(original_guard_class):
            def __init__(self, *args, project="default", **kwargs):
                anchors_path = args[0] if args else "data/anchors.json"
                super().__init__(
                    self.test_path if hasattr(self, "test_path") else anchors_path,
                    project=project,
                )

        TestAnchorGuard.test_path = self.anchors_path
        anchor_module.AnchorGuard = TestAnchorGuard

        try:
            episode_content = "배경만 설명하는 에피소드입니다."
            with pytest.raises(RetryException):
                anchor_module.anchor_guard(episode_content, 1)
        finally:
            # Restore original class
            anchor_module.AnchorGuard = original_guard_class

    def test_anchor_guard_exception_details(self):
        """Test that RetryException contains proper details."""
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "히로인 등장", "anchor_ep": 1},
        ]
        self.create_test_anchors(test_anchors)

        guard = AnchorGuard(self.anchors_path)
        episode_content = "배경만 설명하는 에피소드입니다."

        with pytest.raises(RetryException) as exc_info:
            guard.check(episode_content, 1)

        exception = exc_info.value
        assert exception.guard_name == "anchor_guard"
        assert "anchor_compliance" in exception.flags

        flags = exception.flags["anchor_compliance"]
        assert flags["episode_num"] == 1
        assert flags["total_checked"] == 2
        assert len(flags["missing_anchors"]) == 2

        # Check that missing anchors have the right structure
        for missing in flags["missing_anchors"]:
            assert "id" in missing
            assert "goal" in missing
            assert "anchor_ep" in missing
            assert "keywords" in missing
            assert missing["found"] is False

    def test_anchor_guard_with_no_anchors(self):
        """Test anchor guard behavior with empty anchors list."""
        self.create_test_anchors([])

        guard = AnchorGuard(self.anchors_path)
        episode_content = "어떤 내용이든 상관없습니다."

        result = guard.check(episode_content, 1)
        assert result["passed"] is True
        assert len(result["anchors_checked"]) == 0
        assert len(result["missing_anchors"]) == 0
