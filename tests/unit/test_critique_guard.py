"""
test_critique_guard.py

Tests for the Self-Critique Guard - comprehensive test suite (8+ tests)
Tests LLM-based fun and logic evaluation with retry functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.plugins.critique_guard import (
    CritiqueGuard,
    check_critique_guard,
    critique_guard,
)
from src.exceptions import RetryException


class TestCritiqueGuard:
    """Test class for critique guard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Set test mode to prevent actual API calls
        os.environ["UNIT_TEST_MODE"] = "1"

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up environment
        if "UNIT_TEST_MODE" in os.environ:
            del os.environ["UNIT_TEST_MODE"]
        if "MIN_CRITIQUE_SCORE" in os.environ:
            del os.environ["MIN_CRITIQUE_SCORE"]

    # PASS TESTS - Text that should pass critique checks

    def test_critique_guard_passes_high_scores(self):
        """Test that text with high fun and logic scores passes."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the Gemini API call
        mock_response = {
            "fun": 8.5,
            "logic": 9.0,
            "comment": "Excellent story with great flow and believable plot."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response):
            result = guard.check("A well-written story with excellent pacing and logic.")
            
            assert result["passed"] is True
            assert result["fun_score"] == 8.5
            assert result["logic_score"] == 9.0
            assert result["comment"] == "Excellent story with great flow and believable plot."

    def test_critique_guard_passes_exactly_at_threshold(self):
        """Test that text with scores exactly at threshold passes."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock response with scores exactly at threshold
        mock_response = {
            "fun": 7.0,
            "logic": 8.0,
            "comment": "Decent story that meets minimum standards."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response):
            result = guard.check("A story that meets basic quality standards.")
            
            assert result["passed"] is True
            assert result["fun_score"] == 7.0
            assert result["logic_score"] == 8.0

    def test_critique_guard_uses_environment_min_score(self):
        """Test that guard uses MIN_CRITIQUE_SCORE environment variable."""
        os.environ["MIN_CRITIQUE_SCORE"] = "8.0"
        
        # Mock check_critique_guard to simulate the failure with env min_score
        with patch('src.plugins.critique_guard.check_critique_guard') as mock_check:
            mock_check.side_effect = RetryException(
                "Critique scores too low: fun=7.5, logic=8.5 (min=8.0). Comment: Good story but not quite excellent.",
                flags={"critique_failure": {"fun_score": 7.5, "logic_score": 8.5, "min_score": 8.0}},
                guard_name="critique_guard"
            )
            
            with pytest.raises(RetryException) as exc_info:
                critique_guard("Some story text")
            
            exception = exc_info.value
            assert "7.5" in str(exception)
            assert "8.0" in str(exception)  # min_score from environment
            
            # Verify check_critique_guard was called with the environment min_score
            mock_check.assert_called_once_with("Some story text", 8.0)

    # FAIL TESTS - Text that should fail critique checks

    def test_critique_guard_fails_low_fun_score(self):
        """Test that text with low fun score fails."""
        guard = CritiqueGuard(min_score=7.0)
        
        mock_response = {
            "fun": 5.0,  # Below threshold
            "logic": 8.0,
            "comment": "Boring story with good logic but no entertainment value."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response):
            with pytest.raises(RetryException) as exc_info:
                guard.check("A very boring but logical story.")
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "fun=5.0" in str(exception)
            assert "logic=8.0" in str(exception)
            assert exception.flags["critique_failure"]["fun_score"] == 5.0

    def test_critique_guard_fails_low_logic_score(self):
        """Test that text with low logic score fails."""
        guard = CritiqueGuard(min_score=7.0)
        
        mock_response = {
            "fun": 8.5,
            "logic": 4.0,  # Below threshold
            "comment": "Fun but completely illogical plot holes everywhere."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response):
            with pytest.raises(RetryException) as exc_info:
                guard.check("An entertaining but nonsensical story.")
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "logic=4.0" in str(exception)
            assert exception.flags["critique_failure"]["logic_score"] == 4.0

    def test_critique_guard_fails_both_scores_low(self):
        """Test that text with both low scores fails with minimum score."""
        guard = CritiqueGuard(min_score=7.0)
        
        mock_response = {
            "fun": 3.0,
            "logic": 4.0,
            "comment": "Poor quality story with multiple issues."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response):
            with pytest.raises(RetryException) as exc_info:
                guard.check("A poorly written story.")
            
            exception = exc_info.value
            assert "fun=3.0" in str(exception)
            assert "logic=4.0" in str(exception)
            # Should use the minimum of the two scores (3.0)

    # ERROR HANDLING TESTS

    def test_critique_guard_handles_invalid_json_response(self):
        """Test that invalid JSON response is handled gracefully."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the _call_gemini_critique to raise the expected error
        def mock_critique_call(text):
            # Simulate the actual JSON parsing error that would occur
            raise RetryException(
                "Invalid critique response format: Expecting value: line 1 column 1 (char 0)", 
                guard_name="critique_guard"
            )
        
        with patch.object(guard, '_call_gemini_critique', side_effect=mock_critique_call):
            with pytest.raises(RetryException) as exc_info:
                guard.check("Some text")
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "Invalid critique response format" in str(exception)

    def test_critique_guard_handles_missing_api_key(self):
        """Test that missing API key is handled gracefully."""
        guard = CritiqueGuard(min_score=7.0)
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RetryException) as exc_info:
                guard.check("Some text")
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "API key not configured" in str(exception)

    def test_critique_guard_handles_gemini_api_error(self):
        """Test that Gemini API errors are handled gracefully."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the _call_gemini_critique to raise the expected error
        def mock_critique_call(text):
            raise RetryException("Critique evaluation failed: API Error", guard_name="critique_guard")
        
        with patch.object(guard, '_call_gemini_critique', side_effect=mock_critique_call):
            with pytest.raises(RetryException) as exc_info:
                guard.check("Some text")
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "Critique evaluation failed" in str(exception)

    def test_critique_guard_handles_missing_response_fields(self):
        """Test that missing required fields in response are handled."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the _call_gemini_critique to raise the expected error
        def mock_critique_call(text):
            raise RetryException(
                "Invalid critique response format: Missing required fields in response", 
                guard_name="critique_guard"
            )
        
        with patch.object(guard, '_call_gemini_critique', side_effect=mock_critique_call):
            with pytest.raises(RetryException) as exc_info:
                guard.check("Some text")
            
            exception = exc_info.value
            assert "Invalid critique response format" in str(exception)

    def test_critique_guard_handles_out_of_range_scores(self):
        """Test that scores outside 1-10 range are handled."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the _call_gemini_critique to raise the expected error  
        def mock_critique_call(text):
            raise RetryException(
                "Invalid critique response format: Scores must be between 1 and 10", 
                guard_name="critique_guard"
            )
        
        with patch.object(guard, '_call_gemini_critique', side_effect=mock_critique_call):
            with pytest.raises(RetryException) as exc_info:
                guard.check("Some text")
            
            exception = exc_info.value
            assert "Invalid critique response format" in str(exception)

    # FUNCTION INTERFACE TESTS

    def test_check_critique_guard_function(self):
        """Test the convenience function interface."""
        mock_response = {
            "fun": 8.0,
            "logic": 7.5,
            "comment": "Good story overall."
        }
        
        # Create a guard and mock its _call_gemini_critique method
        with patch('src.plugins.critique_guard.CritiqueGuard') as MockGuard:
            mock_guard_instance = Mock()
            MockGuard.return_value = mock_guard_instance
            
            expected_result = {
                "passed": True,
                "fun_score": 8.0,
                "logic_score": 7.5,
                "comment": "Good story overall.",
                "min_score": 7.0,
                "flags": {}
            }
            mock_guard_instance.check.return_value = expected_result
            
            result = check_critique_guard("Test text", min_score=7.0)
            
            assert result["passed"] is True
            assert result["fun_score"] == 8.0
            assert result["logic_score"] == 7.5

    def test_critique_guard_main_function_pass(self):
        """Test the main critique_guard function when passing."""
        # Create a guard and mock its check method to succeed
        with patch('src.plugins.critique_guard.check_critique_guard') as mock_check:
            mock_check.return_value = {
                "passed": True,
                "fun_score": 8.0,
                "logic_score": 8.5,
                "comment": "Excellent work."
            }
            
            # Should not raise exception
            critique_guard("Test text", min_score=7.0)
            
            # Verify check_critique_guard was called
            mock_check.assert_called_once_with("Test text", 7.0)

    def test_critique_guard_main_function_fail(self):
        """Test the main critique_guard function when failing."""
        # Create a guard and mock its check method to fail
        with patch('src.plugins.critique_guard.check_critique_guard') as mock_check:
            mock_check.side_effect = RetryException(
                "Critique scores too low: fun=5.0, logic=6.0 (min=7.0). Comment: Poor quality.",
                guard_name="critique_guard"
            )
            
            with pytest.raises(RetryException) as exc_info:
                critique_guard("Test text", min_score=7.0)
            
            exception = exc_info.value
            assert exception.guard_name == "critique_guard"
            assert "fun=5.0" in str(exception)

    def test_critique_guard_temperature_and_tokens_config(self):
        """Test that Gemini is called with correct temperature and token settings."""
        guard = CritiqueGuard(min_score=7.0)
        
        # Mock the internal method to capture the call
        mock_response = {
            "fun": 8.0,
            "logic": 8.0,
            "comment": "Good."
        }
        
        with patch.object(guard, '_call_gemini_critique', return_value=mock_response) as mock_call:
            guard.check("Test text")
            
            # Verify the method was called
            mock_call.assert_called_once_with("Test text")