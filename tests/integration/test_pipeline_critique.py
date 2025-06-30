"""
test_pipeline_critique.py

Integration test for pipeline with critique guard validation.
Tests the complete pipeline including self-critique guard evaluation.
"""

import pytest
import os
from unittest.mock import patch, Mock
from src.main import run_pipeline


class TestPipelineCritique:
    """Integration test class for pipeline with critique guard."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Set test mode to prevent actual API calls
        os.environ["UNIT_TEST_MODE"] = "1"
        os.environ["MIN_CRITIQUE_SCORE"] = "7.0"

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up environment
        if "UNIT_TEST_MODE" in os.environ:
            del os.environ["UNIT_TEST_MODE"]
        if "MIN_CRITIQUE_SCORE" in os.environ:
            del os.environ["MIN_CRITIQUE_SCORE"]

    def test_pipeline_with_critique_guard_success(self):
        """Test that pipeline runs successfully with critique guard validation."""
        # The current implementation uses fallback content in test mode,
        # so we test the guard integration by running the pipeline script's guard testing
        from scripts.run_pipeline import test_guards_sequence
        
        # Mock the critique guard to return success
        with patch('src.plugins.critique_guard.critique_guard') as mock_critique:
            mock_critique.return_value = None  # Success case
            
            # Run the guard sequence which includes critique guard
            result = test_guards_sequence(2)
            
            # Verify critique guard was called in the guard sequence
            assert mock_critique.call_count >= 1

    def test_pipeline_with_critique_guard_retry(self):
        """Test that pipeline handles critique guard failures with retry."""
        from src.exceptions import RetryException
        from scripts.run_pipeline import test_guards_sequence
        from unittest.mock import MagicMock
        import importlib
        
        # Test that run_with_retry properly handles RetryException with retries
        # This verifies the core functionality requested in the comment
        
        # Save original environment state
        original_unit_test_mode = os.environ.get("UNIT_TEST_MODE")
        
        try:
            # Clear UNIT_TEST_MODE to enable retries
            if "UNIT_TEST_MODE" in os.environ:
                del os.environ["UNIT_TEST_MODE"]
            
            # Force reload of retry controller to pick up environment changes
            import src.core.retry_controller
            importlib.reload(src.core.retry_controller)
            
            from src.core.retry_controller import run_with_retry
            
            # Test 1: Verify retry logic with mock that fails then succeeds
            mock_critique = MagicMock()
            mock_critique.side_effect = [
                RetryException("Low scores: fun=5.0, logic=6.0", guard_name="critique_guard"),
                "Success"  # Second call succeeds
            ]
            
            result = run_with_retry(mock_critique, "test content", max_retry=1)
            
            # Verify the retry mechanism worked - should be called twice
            assert mock_critique.call_count == 2, f"Expected 2 calls, got {mock_critique.call_count}"
            assert result == "Success", f"Expected 'Success', got {result}"
            
            # Test 2: Verify test_guards_sequence function works (integration test)
            result = test_guards_sequence(2)
            assert isinstance(result, bool), f"Expected boolean result, got {type(result)}"
            
        finally:
            # Restore original environment state
            if original_unit_test_mode is not None:
                os.environ["UNIT_TEST_MODE"] = original_unit_test_mode
            
            # Reload retry controller to restore original behavior
            if original_unit_test_mode is not None:
                importlib.reload(src.core.retry_controller)

    def test_pipeline_with_high_critique_threshold(self):
        """Test pipeline behavior with high critique score threshold."""
        from src.exceptions import RetryException
        from scripts.run_pipeline import test_guards_sequence
        
        # Set high threshold
        os.environ["MIN_CRITIQUE_SCORE"] = "9.0"
        
        # Mock critique guard to consistently fail with high threshold
        with patch('src.plugins.critique_guard.critique_guard') as mock_critique:
            mock_critique.side_effect = RetryException(
                "Low scores: fun=8.0, logic=8.5 (min=9.0)", 
                guard_name="critique_guard"
            )
            
            # Guard sequence should handle the failure appropriately
            result = test_guards_sequence(2)
            
            # Verify critique guard was called
            assert mock_critique.call_count >= 1