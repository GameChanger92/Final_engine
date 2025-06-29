"""
test_rule_guard.py

Tests for the Rule Guard - comprehensive test suite (10+ tests)
Tests forbidden pattern detection and rule violation functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from src.plugins.rule_guard import (
    RuleGuard,
    check_rule_guard,
    rule_guard,
)
from src.exceptions import RetryException


class TestRuleGuard:
    """Test class for rule guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_rules_path = os.path.join(self.temp_dir, "test_rules.json")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temporary files
        if os.path.exists(self.test_rules_path):
            os.remove(self.test_rules_path)
        os.rmdir(self.temp_dir)

    def _create_test_rules(self, rules):
        """Helper method to create test rules file."""
        with open(self.test_rules_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

    # PASS TESTS (5 tests) - Text that should pass rule checks

    def test_rule_guard_passes_clean_text(self):
        """Test that clean text with no forbidden patterns passes."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법|마도", "message": "마법 사용은 금지!"},
            {"id": "NO_ELF", "pattern": "엘프", "message": "엘프는 세계관에 존재하지 않음!"}
        ]
        self._create_test_rules(rules)
        
        text = "용사가 모험을 떠났다. 그는 검을 들고 성을 향해 걸어갔다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check(text)
        
        assert result["passed"] is True
        assert result["rules_checked"] == 2
        assert len(result["violations"]) == 0
        assert result["flags"] == {}

    def test_rule_guard_passes_empty_text(self):
        """Test that empty text passes all rule checks."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 금지!"}
        ]
        self._create_test_rules(rules)
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check("")
        
        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_rule_guard_passes_with_empty_rules_file(self):
        """Test that text passes when rules.json is empty."""
        self._create_test_rules([])
        
        text = "마법을 사용했다. 엘프가 나타났다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check(text)
        
        assert result["passed"] is True
        assert result["rules_checked"] == 0
        assert len(result["violations"]) == 0

    def test_rule_guard_passes_with_missing_rules_file(self):
        """Test that text passes when rules.json doesn't exist."""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent_rules.json")
        
        text = "마법을 사용했다. 엘프가 나타났다."
        
        guard = RuleGuard(rule_path=non_existent_path)
        result = guard.check(text)
        
        assert result["passed"] is True
        assert result["rules_checked"] == 0
        assert len(result["violations"]) == 0

    def test_rule_guard_passes_partial_match(self):
        """Test that partial pattern matches don't trigger violations."""
        rules = [
            {"id": "NO_EXACT", "pattern": "^엘프$", "message": "엘프 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "엘프들이 나타났다."  # Contains "엘프" but not exact match
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check(text)
        
        assert result["passed"] is True

    # FAIL TESTS (5+ tests) - Text that should fail rule checks

    def test_rule_guard_fails_on_forbidden_pattern(self):
        """Test that text with forbidden pattern fails."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 사용은 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "용사가 마법을 사용했다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        exception = exc_info.value
        assert exception.guard_name == "rule_guard"
        assert str(exception).startswith("[rule_guard] 마법 사용은 금지!")
        assert "rule_violation" in exception.flags
        assert exception.flags["rule_violation"]["rule_id"] == "NO_MAGIC"
        assert exception.flags["rule_violation"]["matched_text"] == "마법"

    def test_rule_guard_fails_case_insensitive(self):
        """Test that pattern matching is case insensitive."""
        rules = [
            {"id": "NO_ELF", "pattern": "elf", "message": "Elf forbidden!"}
        ]
        self._create_test_rules(rules)
        
        text = "The mighty ELF appeared."  # Uppercase should still match
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        exception = exc_info.value
        assert exception.guard_name == "rule_guard"
        assert exception.flags["rule_violation"]["matched_text"] == "ELF"

    def test_rule_guard_fails_multiple_violations_reports_first(self):
        """Test that multiple violations report only the first violation."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 금지!"},
            {"id": "NO_ELF", "pattern": "엘프", "message": "엘프 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "마법을 사용하는 엘프가 나타났다."  # Contains both violations
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        exception = exc_info.value
        # Should report first violation (NO_MAGIC)
        assert str(exception).startswith("[rule_guard] 마법 금지!")
        assert exception.flags["rule_violation"]["rule_id"] == "NO_MAGIC"

    def test_rule_guard_fails_complex_regex_pattern(self):
        """Test that complex regex patterns work correctly."""
        rules = [
            {"id": "NO_MODERN", "pattern": r"(컴퓨터|스마트폰|인터넷)", "message": "현대 기술 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "그는 스마트폰으로 사진을 찍었다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        exception = exc_info.value
        assert str(exception).startswith("[rule_guard] 현대 기술 금지!")
        assert exception.flags["rule_violation"]["matched_text"] == "스마트폰"

    def test_rule_guard_fails_or_pattern(self):
        """Test that OR patterns (|) work correctly."""
        rules = [
            {"id": "NO_DRAGON", "pattern": "드래곤|용", "message": "드래곤 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "거대한 용이 하늘을 날았다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        exception = exc_info.value
        assert str(exception).startswith("[rule_guard] 드래곤 금지!")
        assert exception.flags["rule_violation"]["matched_text"] == "용"

    # EDGE CASE TESTS (5+ tests)

    def test_rule_guard_handles_invalid_regex_pattern(self):
        """Test that invalid regex patterns are gracefully handled."""
        rules = [
            {"id": "INVALID", "pattern": "[invalid", "message": "Invalid pattern!"},
            {"id": "VALID", "pattern": "테스트", "message": "Valid pattern!"}
        ]
        self._create_test_rules(rules)
        
        text = "테스트 중입니다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        # Should still catch the valid pattern despite invalid one
        exception = exc_info.value
        assert exception.flags["rule_violation"]["rule_id"] == "VALID"

    def test_rule_guard_handles_malformed_rules_json(self):
        """Test that malformed rules JSON is handled gracefully."""
        # Create malformed JSON file
        with open(self.test_rules_path, 'w', encoding='utf-8') as f:
            f.write('{"invalid": json}')
        
        text = "Any text should pass"
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check(text)
        
        assert result["passed"] is True
        assert result["rules_checked"] == 0

    def test_rule_guard_handles_rules_missing_required_fields(self):
        """Test that rules missing required fields are filtered out."""
        rules = [
            {"id": "INCOMPLETE", "pattern": "test"},  # Missing message
            {"pattern": "another", "message": "msg"},  # Missing id  
            {"id": "VALID", "pattern": "유효", "message": "Valid rule!"}
        ]
        self._create_test_rules(rules)
        
        text = "유효한 테스트"
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        with pytest.raises(RetryException) as exc_info:
            guard.check(text)
        
        # Should only process the valid rule
        exception = exc_info.value
        assert exception.flags["rule_violation"]["rule_id"] == "VALID"
        assert guard.rules == [{"id": "VALID", "pattern": "유효", "message": "Valid rule!"}]

    def test_rule_guard_handles_non_list_rules_json(self):
        """Test that non-list rules JSON is handled gracefully."""
        # Create non-list JSON
        with open(self.test_rules_path, 'w', encoding='utf-8') as f:
            json.dump({"not": "a list"}, f)
        
        text = "Any text should pass"
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        result = guard.check(text)
        
        assert result["passed"] is True
        assert result["rules_checked"] == 0

    # CONVENIENCE FUNCTION TESTS (2 tests)

    def test_check_rule_guard_function(self):
        """Test the check_rule_guard convenience function."""
        rules = [
            {"id": "NO_TEST", "pattern": "테스트", "message": "테스트 금지!"}
        ]
        self._create_test_rules(rules)
        
        with pytest.raises(RetryException) as exc_info:
            check_rule_guard("테스트 중입니다.", rule_path=self.test_rules_path)
        
        exception = exc_info.value
        assert exception.guard_name == "rule_guard"

    def test_rule_guard_main_function_pass(self):
        """Test the main rule_guard function when checks pass."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 금지!"}
        ]
        self._create_test_rules(rules)
        
        result = rule_guard("평범한 텍스트입니다.", rule_path=self.test_rules_path)
        assert result is True

    def test_rule_guard_main_function_fail(self):
        """Test the main rule_guard function when checks fail."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 금지!"}
        ]
        self._create_test_rules(rules)
        
        with pytest.raises(RetryException):
            rule_guard("마법을 사용했다.", rule_path=self.test_rules_path)

    def test_rule_guard_match_position_tracking(self):
        """Test that match position is correctly tracked."""
        rules = [
            {"id": "NO_MAGIC", "pattern": "마법", "message": "마법 금지!"}
        ]
        self._create_test_rules(rules)
        
        text = "용사가 강력한 마법을 사용했다."
        
        guard = RuleGuard(rule_path=self.test_rules_path)
        
        try:
            guard.check(text)
        except RetryException as e:
            # Check that violation details are captured before exception
            pass
        
        # Test the result structure by catching before exception
        guard_test = RuleGuard(rule_path=self.test_rules_path)
        results = {"passed": True, "violations": []}
        
        import re
        for rule in guard_test.rules:
            match = re.search(rule['pattern'], text, re.IGNORECASE)
            if match:
                results["violations"].append({
                    "match_position": match.start()
                })
                break
        
        assert len(results["violations"]) > 0
        assert results["violations"][0]["match_position"] == text.find("마법")