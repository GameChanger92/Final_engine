"""
test_foreshadow_scheduler.py

Tests for the Foreshadow Scheduler - comprehensive test suite.
Tests foreshadow creation, ID uniqueness, due calculation, and payoff tracking.
"""

import json
import os
import tempfile
from unittest.mock import patch

from src.plugins.foreshadow_scheduler import (
    _calculate_due_episode,
    _generate_unique_id,
    _load_foreshadows,
    get_foreshadows,
    get_overdue_foreshadows,
    get_unresolved_foreshadows,
    schedule_foreshadow,
    track_payoff,
)


class TestForeshadowScheduler:
    """Test class for foreshadow scheduler functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "foreshadow.json")

        # Patch the file path to use our temporary file
        self.file_path_patcher = patch("src.plugins.foreshadow_scheduler._get_foreshadow_file_path")
        self.mock_file_path = self.file_path_patcher.start()
        self.mock_file_path.return_value = self.test_file

    def teardown_method(self):
        """Clean up after each test."""
        self.file_path_patcher.stop()
        # Clean up temporary files
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_schedule_foreshadow_basic(self):
        """Test basic foreshadow scheduling functionality."""
        hint = "신비한 검의 존재"
        introduced_ep = 5

        result = schedule_foreshadow(hint, introduced_ep)

        # Check return value structure
        assert isinstance(result, dict)
        assert "id" in result
        assert "hint" in result
        assert "introduced" in result
        assert "due" in result
        assert "payoff" in result

        # Check values
        assert result["hint"] == hint
        assert result["introduced"] == introduced_ep
        assert result["payoff"] is None
        assert result["id"].startswith("f")
        assert len(result["id"]) == 7  # "f" + 6 characters

        # Check due episode is within expected range
        assert introduced_ep + 10 <= result["due"] <= introduced_ep + 30
        assert result["due"] <= 250  # Should not exceed TOTAL_EPISODES

    def test_schedule_foreshadow_file_persistence(self):
        """Test that foreshadows are properly saved to file."""
        hint1 = "첫 번째 복선"
        hint2 = "두 번째 복선"

        # Create two foreshadows
        foreshadow1 = schedule_foreshadow(hint1, 3)
        foreshadow2 = schedule_foreshadow(hint2, 7)

        # Verify file exists and contains both foreshadows
        assert os.path.exists(self.test_file)

        with open(self.test_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "foreshadows" in data
        assert len(data["foreshadows"]) == 2

        # Check that both foreshadows are present
        ids = [f["id"] for f in data["foreshadows"]]
        assert foreshadow1["id"] in ids
        assert foreshadow2["id"] in ids

    def test_schedule_foreshadow_unique_ids(self):
        """Test that foreshadow IDs are unique."""
        hints = [f"복선 {i}" for i in range(10)]
        foreshadows = []

        for i, hint in enumerate(hints):
            foreshadow = schedule_foreshadow(hint, i + 1)
            foreshadows.append(foreshadow)

        # Check all IDs are unique
        ids = [f["id"] for f in foreshadows]
        assert len(ids) == len(set(ids))  # No duplicates

        # Check all IDs follow the pattern
        for foreshadow_id in ids:
            assert foreshadow_id.startswith("f")
            assert len(foreshadow_id) == 7

    def test_track_payoff_basic(self):
        """Test basic payoff tracking functionality."""
        # Create a foreshadow
        foreshadow = schedule_foreshadow("검의 비밀", 5)
        foreshadow_id = foreshadow["id"]

        # Create content with resolution pattern
        content = f"마침내 진실이 밝혀졌다. [RESOLVED:{foreshadow_id}] 모든 것이 명확해졌다."

        # Track payoff
        result = track_payoff(25, content)

        assert result is True

        # Check that foreshadow was marked as resolved
        foreshadows = get_foreshadows()
        resolved_foreshadow = next(f for f in foreshadows if f["id"] == foreshadow_id)
        assert resolved_foreshadow["payoff"] == 25

    def test_track_payoff_no_matches(self):
        """Test payoff tracking when no resolution patterns are found."""
        # Create a foreshadow
        schedule_foreshadow("검의 비밀", 5)

        # Create content without resolution pattern
        content = "일반적인 에피소드 내용입니다."

        # Track payoff
        result = track_payoff(25, content)

        assert result is False

        # Check that no foreshadows were resolved
        unresolved = get_unresolved_foreshadows()
        assert len(unresolved) == 1

    def test_track_payoff_multiple_resolutions(self):
        """Test tracking multiple payoffs in single content."""
        # Create multiple foreshadows
        foreshadow1 = schedule_foreshadow("첫 번째 복선", 3)
        foreshadow2 = schedule_foreshadow("두 번째 복선", 7)
        foreshadow3 = schedule_foreshadow("세 번째 복선", 10)

        # Create content with multiple resolutions
        content = f"""
        이번 에피소드에서 많은 것이 해결되었다.
        [RESOLVED:{foreshadow1["id"]}] 첫 번째 미스터리가 풀렸고,
        [RESOLVED:{foreshadow3["id"]}] 세 번째 수수께끼도 해결되었다.
        하지만 두 번째는 아직 남아있다.
        """

        # Track payoff
        result = track_payoff(20, content)

        assert result is True

        # Check that correct foreshadows were resolved
        foreshadows = get_foreshadows()
        foreshadow_dict = {f["id"]: f for f in foreshadows}

        assert foreshadow_dict[foreshadow1["id"]]["payoff"] == 20
        assert foreshadow_dict[foreshadow2["id"]]["payoff"] is None  # Still unresolved
        assert foreshadow_dict[foreshadow3["id"]]["payoff"] == 20

    def test_track_payoff_already_resolved(self):
        """Test that already resolved foreshadows are not re-resolved."""
        # Create a foreshadow
        foreshadow = schedule_foreshadow("검의 비밀", 5)
        foreshadow_id = foreshadow["id"]

        # Resolve it first time
        content1 = f"첫 번째 해결. [RESOLVED:{foreshadow_id}]"
        result1 = track_payoff(20, content1)
        assert result1 is True

        # Try to resolve again
        content2 = f"두 번째 해결 시도. [RESOLVED:{foreshadow_id}]"
        result2 = track_payoff(25, content2)
        assert result2 is False  # Should not count as new resolution

        # Check payoff episode didn't change
        foreshadows = get_foreshadows()
        resolved_foreshadow = next(f for f in foreshadows if f["id"] == foreshadow_id)
        assert resolved_foreshadow["payoff"] == 20  # Still the original episode

    def test_get_unresolved_foreshadows(self):
        """Test getting unresolved foreshadows."""
        # Create mixed resolved/unresolved foreshadows
        foreshadow1 = schedule_foreshadow("해결된 복선", 3)
        foreshadow2 = schedule_foreshadow("미해결 복선", 7)
        foreshadow3 = schedule_foreshadow("또 다른 미해결", 10)

        # Resolve one
        content = f"해결됨. [RESOLVED:{foreshadow1['id']}]"
        track_payoff(15, content)

        # Get unresolved
        unresolved = get_unresolved_foreshadows()

        assert len(unresolved) == 2
        unresolved_ids = [f["id"] for f in unresolved]
        assert foreshadow2["id"] in unresolved_ids
        assert foreshadow3["id"] in unresolved_ids
        assert foreshadow1["id"] not in unresolved_ids

    def test_get_overdue_foreshadows(self):
        """Test getting overdue foreshadows."""
        # Create foreshadows with different due episodes
        with patch("src.plugins.foreshadow_scheduler._calculate_due_episode") as mock_calc:
            # Mock specific due episodes
            mock_calc.side_effect = [15, 25, 35]  # Different due episodes

            foreshadow1 = schedule_foreshadow("곧 만료", 5)  # due = 15
            foreshadow2 = schedule_foreshadow("나중 만료", 10)  # due = 25
            foreshadow3 = schedule_foreshadow("미래 만료", 15)  # due = 35

        # Check overdue at episode 20
        overdue = get_overdue_foreshadows(20)

        assert len(overdue) == 1
        assert overdue[0]["id"] == foreshadow1["id"]

        # Check overdue at episode 30
        overdue = get_overdue_foreshadows(30)

        assert len(overdue) == 2
        overdue_ids = [f["id"] for f in overdue]
        assert foreshadow1["id"] in overdue_ids
        assert foreshadow2["id"] in overdue_ids
        assert foreshadow3["id"] not in overdue_ids

    def test_due_episode_calculation_limits(self):
        """Test that due episode calculation respects total episode limit."""
        # Test with high introduced episode
        due1 = _calculate_due_episode(240, total_episodes=250)
        assert due1 <= 250

        # Test with very high introduced episode
        due2 = _calculate_due_episode(245, total_episodes=250)
        assert due2 <= 250

        # Test with normal introduced episode
        due3 = _calculate_due_episode(50, total_episodes=250)
        assert 60 <= due3 <= 80  # Should be introduced + 10-30

    def test_generate_unique_id_format(self):
        """Test unique ID generation format."""
        existing_ids = []

        for _ in range(10):
            new_id = _generate_unique_id(existing_ids)
            assert new_id.startswith("f")
            assert len(new_id) == 7
            assert new_id not in existing_ids
            existing_ids.append(new_id)

    def test_generate_unique_id_collision_handling(self):
        """Test ID generation handles collisions."""
        # Create a large list of existing IDs to force collision scenarios
        existing_ids = [f"f{i:06d}" for i in range(100)]

        new_id = _generate_unique_id(existing_ids)
        assert new_id not in existing_ids
        assert new_id.startswith("f")
        assert len(new_id) == 7

    def test_file_operations_nonexistent_file(self):
        """Test that operations work when foreshadow.json doesn't exist."""
        # Ensure file doesn't exist
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

        # Try to load from non-existent file
        data = _load_foreshadows()
        assert data == {"foreshadows": []}

        # Schedule a foreshadow (should create file)
        foreshadow = schedule_foreshadow("새로운 복선", 5)
        assert os.path.exists(self.test_file)

        # Verify file contents
        with open(self.test_file, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert len(saved_data["foreshadows"]) == 1
        assert saved_data["foreshadows"][0]["id"] == foreshadow["id"]

    def test_file_operations_corrupted_file(self):
        """Test that operations handle corrupted JSON gracefully."""
        # Create corrupted JSON file
        with open(self.test_file, "w") as f:
            f.write("{ invalid json }")

        # Try to load corrupted file
        data = _load_foreshadows()
        assert data == {"foreshadows": []}

        # Schedule a foreshadow (should overwrite corrupted file)
        foreshadow = schedule_foreshadow("복구된 복선", 5)

        # Verify file is now valid
        with open(self.test_file, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert len(saved_data["foreshadows"]) == 1
        assert saved_data["foreshadows"][0]["id"] == foreshadow["id"]


# Additional edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_hint(self):
        """Test scheduling foreshadow with empty hint."""
        result = schedule_foreshadow("", 5)
        assert result["hint"] == ""
        assert result["introduced"] == 5

    def test_zero_episode(self):
        """Test scheduling foreshadow at episode 0."""
        result = schedule_foreshadow("시작 복선", 0)
        assert result["introduced"] == 0
        assert 10 <= result["due"] <= 30

    def test_negative_episode(self):
        """Test scheduling foreshadow with negative episode."""
        result = schedule_foreshadow("과거 복선", -5)
        assert result["introduced"] == -5
        # Due should still be calculated normally
        assert 5 <= result["due"] <= 25

    def test_track_payoff_empty_content(self):
        """Test tracking payoff with empty content."""
        schedule_foreshadow("빈 내용 테스트", 5)
        result = track_payoff(10, "")
        assert result is False

    def test_track_payoff_malformed_pattern(self):
        """Test tracking payoff with malformed resolution patterns."""
        foreshadow = schedule_foreshadow("잘못된 패턴", 5)

        # Test various malformed patterns
        malformed_contents = [
            f"RESOLVED:{foreshadow['id']}",  # Missing brackets
            f"[RESOLVED{foreshadow['id']}]",  # Missing colon
            "[RESOLVED:]",  # Missing ID
            "[RESOLVED:INVALID]",  # Invalid ID
            f"[RESOLVED: {foreshadow['id']} ]",  # Extra spaces
        ]

        for content in malformed_contents:
            result = track_payoff(10, content)
            # Only the invalid ID case should return False
            if "INVALID" in content:
                assert result is False
            elif f"[RESOLVED:{foreshadow['id']}]" not in content:
                assert result is False

    def test_unicode_hint(self):
        """Test scheduling foreshadow with unicode characters."""
        unicode_hint = "🔮 마법의 수정구 ✨"
        result = schedule_foreshadow(unicode_hint, 10)
        assert result["hint"] == unicode_hint

        # Test that it saves and loads correctly
        foreshadows = get_foreshadows()
        saved_hint = next(f["hint"] for f in foreshadows if f["id"] == result["id"])
        assert saved_hint == unicode_hint
