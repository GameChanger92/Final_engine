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
        from unittest.mock import patch, MagicMock
        import sys
        import importlib
        
        # Enable retries for this test by setting UNIT_TEST_MODE to 0
        original_unit_test_mode = os.environ.get("UNIT_TEST_MODE")
        os.environ["UNIT_TEST_MODE"] = "0"  # Explicitly disable test mode for retry test
        
        try:
            # Directly patch the critique_guard module
            with patch.dict('sys.modules', {'src.plugins.critique_guard': MagicMock()}):
                mock_critique = MagicMock()
                mock_critique.side_effect = [
                    RetryException("Low scores: fun=5.0, logic=6.0", guard_name="critique_guard"),
                    None  # Success on retry
                ]
                
                # Set the critique_guard function on the mocked module
                sys.modules['src.plugins.critique_guard'].critique_guard = mock_critique
                
                # Force reload the run_pipeline module to use our mock
                if 'scripts.run_pipeline' in sys.modules:
                    importlib.reload(sys.modules['scripts.run_pipeline'])
                
                from scripts.run_pipeline import test_guards_sequence
                
                # Run the guard sequence 
                result = test_guards_sequence(2)
                
                # Verify critique guard was called multiple times due to retry
                assert mock_critique.call_count >= 2
                
        finally:
            # Restore original state
            if original_unit_test_mode is not None:
                os.environ["UNIT_TEST_MODE"] = original_unit_test_mode
            elif "UNIT_TEST_MODE" in os.environ:
                del os.environ["UNIT_TEST_MODE"]

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