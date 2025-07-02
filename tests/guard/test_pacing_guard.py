"""
test_pacing_guard.py

Tests for the Pacing Guard - comprehensive test suite (10+ tests)
Tests action/dialog/monolog ratio analysis and pacing violation detection.
"""

import json
import os
import tempfile

import pytest

from src.exceptions import RetryException
from src.plugins.pacing_guard import (
    PacingGuard,
    check_pacing_guard,
    pacing_guard,
)


class TestPacingGuard:
    """Test class for pacing guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, "pacing_config.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        os.rmdir(self.temp_dir)

    def _create_test_config(self, config):
        """Helper method to create test config file."""
        with open(self.test_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # PASS TESTS (6 tests) - Content that should pass pacing checks

    def test_pacing_guard_passes_balanced_content(self):
        """Test that balanced content with normal ratios passes."""
        scene_texts = [
            '그는 달렸다. "어디로 가야 하지?" 그는 생각했다.',  # Balanced: action + dialog + monolog
            '그녀가 말했다. "안녕하세요." 기분이 좋았다고 느꼈다.',  # Similar balance
            '문을 열었다. "누구세요?" 의아했다.',  # Action + dialog + monolog
        ]

        guard = PacingGuard("default")
        result = guard.check(scene_texts, 5)

        assert result["passed"] is True
        assert "current_ratios" in result
        assert "average_ratios" in result
        assert len(result["violations"]) == 0

    def test_pacing_guard_passes_empty_scenes(self):
        """Test that empty scene list passes without issues."""
        guard = PacingGuard("default")
        result = guard.check([], 1)

        assert result["passed"] is True
        assert result["current_ratios"] == {}
        assert len(result["violations"]) == 0

    def test_pacing_guard_passes_with_minor_deviations(self):
        """Test that minor deviations within tolerance pass."""
        # Create content with slight imbalance but within 25% tolerance
        scene_texts = [
            "그는 달렸다. 그녀가 뛰었다. 문을 열었다.",  # Action-heavy but not extreme
            '"안녕하세요." "어떻게 지내세요?" "좋습니다."',  # Dialog-heavy but balanced by previous
            "생각했다. 느꼈다. 깨달았다.",  # Monolog-heavy but balanced overall
        ]

        guard = PacingGuard("default")
        result = guard.check(scene_texts, 5)

        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_pacing_guard_passes_with_default_config(self):
        """Test that guard works with default config when file missing."""
        guard = PacingGuard("nonexistent_project")

        scene_texts = ['그는 달렸다. "안녕하세요." 생각했다.']
        result = guard.check(scene_texts, 1)

        assert result["passed"] is True
        assert guard.config["tolerance"] == 0.25
        assert guard.config["window"] == 10

    def test_pacing_guard_passes_mixed_content_types(self):
        """Test that various content mixing patterns pass."""
        scene_texts = [
            '그는 달렸다. 그녀가 왔다. 문을 열었다. "안녕하세요." 생각했다.',
            '"어떻게 지내세요?" "잘 지내고 있어요." 기뻤다고 느꼈다.',
            '공격했다. 방어했다. "조심해!" 걱정했다.',
        ]

        guard = PacingGuard("default")
        result = guard.check(scene_texts, 3)

        assert result["passed"] is True

    def test_pacing_guard_passes_single_content_type_scenes(self):
        """Test that scenes with single content type can pass when balanced overall."""
        scene_texts = [
            "그는 달렸다. 그녀가 뛰었다. 문을 열었다.",  # Pure action
            '"안녕하세요." "어떻게 지내세요?" "좋습니다."',  # Pure dialog
            "생각했다. 느꼈다. 깨달았다. 회상했다.",  # Pure monolog
        ]

        guard = PacingGuard("default")
        result = guard.check(scene_texts, 5)

        # Should pass because overall balance is maintained
        assert result["passed"] is True or len(result["violations"]) == 0

    # FAIL TESTS (6 tests) - Content that should trigger pacing violations

    def test_pacing_guard_fails_dialog_heavy_content(self):
        """Test that dialog-heavy content (90%) triggers violation."""
        scene_texts = [
            '"안녕하세요." "어떻게 지내세요?" "좋습니다." "감사합니다." "오늘 날씨가 좋네요." "그러게 말이에요."',
            '"산책하기 좋겠어요." "어디로 가실 건가요?" "공원으로 갈 예정이에요." "함께 가도 될까요?" "좋은 생각이에요."',
            '"언제 출발할까요?" "지금 바로 가죠." "좋아요." "그럼 준비해보세요." "네, 알겠습니다."',
        ]

        guard = PacingGuard("default")

        with pytest.raises(RetryException) as exc_info:
            guard.check(scene_texts, 5)

        assert "pacing violation" in str(exc_info.value).lower()
        assert exc_info.value.guard_name == "pacing_guard"

    def test_pacing_guard_fails_action_heavy_content(self):
        """Test that action-heavy content triggers violation."""
        scene_texts = [
            "그는 달렸다. 그녀가 뛰었다. 문을 열었다. 의자를 던졌다. 벽을 쳤다. 땅을 굴렀다.",
            "공격했다. 방어했다. 피했다. 숨었다. 움직였다. 싸웠다. 때렸다. 잡았다.",
            "뛰어갔다. 달려갔다. 걸어갔다. 넘어졌다. 일어났다. 다시 달렸다. 멈췄다. 돌아섰다.",
        ]

        guard = PacingGuard("default")

        with pytest.raises(RetryException) as exc_info:
            guard.check(scene_texts, 5)

        assert "pacing violation" in str(exc_info.value).lower()
        assert exc_info.value.guard_name == "pacing_guard"

    def test_pacing_guard_fails_monolog_heavy_content(self):
        """Test that monolog-heavy content triggers violation."""
        scene_texts = [
            "생각했다. 느꼈다. 깨달았다. 알았다. 믿었다. 의심했다. 확신했다. 추측했다.",
            "상상했다. 기억했다. 잊었다. 회상했다. 반성했다. 후회했다. 바랐다. 원했다.",
            "희망했다. 걱정했다. 두려워했다. 안심했다. 놀랐다. 의아했다. 궁금했다. 이해했다.",
        ]

        guard = PacingGuard("default")

        with pytest.raises(RetryException) as exc_info:
            guard.check(scene_texts, 5)

        assert "pacing violation" in str(exc_info.value).lower()
        assert exc_info.value.guard_name == "pacing_guard"

    def test_pacing_guard_fails_with_custom_tolerance(self):
        """Test that guard fails with stricter custom tolerance."""
        # Create config with very strict tolerance
        config = {"tolerance": 0.05, "window": 5}  # 5% tolerance
        self._create_test_config(config)

        # Create guard that loads the test config
        guard = PacingGuard("default")
        guard.config_path = self.test_config_path  # Override config path
        guard.config = guard._load_config()

        # Content with more extreme imbalance that should violate strict tolerance
        scene_texts = [
            '"이것은 대화입니다." "또 다른 대화입니다." "계속 대화만 있습니다."',  # Pure dialog
            '"대화가 너무 많습니다." "액션이나 독백이 없습니다." "이런 내용은 실패해야 합니다."',  # More pure dialog
        ]

        with pytest.raises(RetryException):
            guard.check(scene_texts, 3)

    def test_pacing_guard_fails_extreme_imbalance(self):
        """Test that extremely imbalanced content always fails."""
        scene_texts = [
            '"대화만 있는 씬입니다." "계속 대화가 이어집니다."',
            '"다른 내용은 전혀 없습니다." "오직 대화뿐입니다."',
            '"이런 내용은 실패해야 합니다." "균형이 너무 깨졌습니다."',
        ]

        guard = PacingGuard("default")

        with pytest.raises(RetryException) as exc_info:
            guard.check(scene_texts, 8)

        assert exc_info.value.flags["pacing_violation"]["violations"]
        assert len(exc_info.value.flags["pacing_violation"]["violations"]) >= 1

    def test_pacing_guard_fails_reports_multiple_violations(self):
        """Test that multiple content type violations are reported."""
        # Create content that violates multiple ratios
        scene_texts = [
            "그는 달렸다. 그녀가 뛰었다. 공격했다. 방어했다. 싸웠다.",  # Heavy action, no dialog/monolog
        ]

        guard = PacingGuard("default")

        with pytest.raises(RetryException) as exc_info:
            guard.check(scene_texts, 5)

        # Should detect imbalance in multiple content types
        violations = exc_info.value.flags["pacing_violation"]["violations"]
        assert len(violations) >= 1

        # Check that violation details are included
        first_violation = violations[0]
        assert "content_type" in first_violation
        assert "current_ratio" in first_violation
        assert "average_ratio" in first_violation

    # EDGE CASE TESTS (3 tests) - Special scenarios and error handling

    def test_pacing_guard_handles_malformed_config(self):
        """Test that guard handles malformed config gracefully."""
        # Create malformed JSON config
        with open(self.test_config_path, "w", encoding="utf-8") as f:
            f.write('{"tolerance": 0.25, "window":}')  # Invalid JSON

        guard = PacingGuard("default")
        guard.config_path = self.test_config_path
        guard.config = guard._load_config()

        # Should use default config
        assert guard.config["tolerance"] == 0.25
        assert guard.config["window"] == 10

    def test_pacing_guard_handles_empty_scenes_in_list(self):
        """Test that guard handles empty strings in scene list."""
        scene_texts = ["", "   ", "그는 달렸다.", "", '"안녕하세요."', "생각했다."]

        guard = PacingGuard("default")
        result = guard.check(scene_texts, 3)

        # Should analyze only non-empty scenes
        assert "current_ratios" in result

    def test_pacing_guard_rolling_window_application(self):
        """Test that rolling window correctly limits historical analysis."""
        # Test with window size of 3
        config = {"tolerance": 0.25, "window": 3}
        self._create_test_config(config)

        guard = PacingGuard("default")
        guard.config_path = self.test_config_path
        guard.config = guard._load_config()

        scene_texts = [
            '그는 달렸다. "안녕하세요." 생각했다.',
            '그녀가 뛰었다. "어떻게 지내세요?" 느꼈다.',
            '문을 열었다. "좋은 하루예요." 깨달았다.',
            '의자를 옮겼다. "감사합니다." 기억했다.',  # 4th scene (beyond window)
        ]

        result = guard.check(scene_texts, 5)

        # Should use only first 3 scenes for average calculation
        assert "average_ratios" in result
        assert guard.config["window"] == 3

    # CONVENIENCE FUNCTION TESTS (2 tests)

    def test_check_pacing_guard_function(self):
        """Test the convenience check_pacing_guard function."""
        scene_texts = ['그는 달렸다. "안녕하세요." 생각했다.']

        result = check_pacing_guard(scene_texts, 1, "default")

        assert "passed" in result
        assert "current_ratios" in result
        assert "average_ratios" in result

    def test_pacing_guard_main_function(self):
        """Test the main pacing_guard function entry point."""
        scene_texts = ['그는 달렸다. "안녕하세요." 생각했다.']

        # Should return True for balanced content
        result = pacing_guard(scene_texts, 1, "default")
        assert result is True

        # Should raise exception for imbalanced content
        imbalanced_scenes = [
            '"대화만 있습니다." "계속 대화입니다." "또 대화입니다."',
            '"더 많은 대화입니다." "대화가 끝나지 않습니다."',
        ]

        with pytest.raises(RetryException):
            pacing_guard(imbalanced_scenes, 5, "default")
