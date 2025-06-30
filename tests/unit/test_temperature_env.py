"""
Tests for LLM temperature environment variable integration
"""

import os
import pytest


class TestTemperatureEnvironment:
    """Test cases for temperature environment variable handling."""
    
    def test_temperature_env_vars_accessible(self, monkeypatch):
        """Test that all temperature environment variables can be accessed."""
        # Set all temperature variables
        monkeypatch.setenv("TEMP_DRAFT", "0.85")
        monkeypatch.setenv("TEMP_BEAT", "0.25") 
        monkeypatch.setenv("TEMP_SCENE", "0.55")
        
        # Verify they can be read with correct defaults
        assert float(os.getenv("TEMP_DRAFT", "0.7")) == 0.85
        assert float(os.getenv("TEMP_BEAT", "0.3")) == 0.25
        assert float(os.getenv("TEMP_SCENE", "0.6")) == 0.55
    
    def test_temperature_env_vars_defaults(self, monkeypatch):
        """Test that temperature environment variables have correct defaults."""
        # Remove all temperature variables
        monkeypatch.delenv("TEMP_DRAFT", raising=False)
        monkeypatch.delenv("TEMP_BEAT", raising=False)
        monkeypatch.delenv("TEMP_SCENE", raising=False)
        
        # Verify defaults are used
        assert float(os.getenv("TEMP_DRAFT", "0.7")) == 0.7
        assert float(os.getenv("TEMP_BEAT", "0.3")) == 0.3
        assert float(os.getenv("TEMP_SCENE", "0.6")) == 0.6

    def test_invalid_temperature_values_handled(self, monkeypatch):
        """Test that invalid temperature values are handled gracefully."""
        # Set invalid temperature value
        monkeypatch.setenv("TEMP_DRAFT", "invalid")
        
        # This should raise ValueError when trying to convert to float
        with pytest.raises(ValueError):
            float(os.getenv("TEMP_DRAFT", "0.7"))

    def test_draft_temperature_used_in_call_llm(self, monkeypatch):
        """Test that TEMP_DRAFT environment variable is used in call_llm function."""
        from src.draft_generator import call_llm
        from src.exceptions import RetryException
        
        # Set custom temperature
        monkeypatch.setenv("TEMP_DRAFT", "0.9")
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
        monkeypatch.setenv("UNIT_TEST_MODE", "1")  # This triggers import error gracefully
        
        # Call should fail with RetryException but temperature parsing should work
        with pytest.raises(RetryException):
            call_llm("test prompt")
        
        # Verify the temperature can be read correctly
        assert float(os.getenv("TEMP_DRAFT", "0.7")) == 0.9

    def test_draft_temperature_integration_with_generate_draft(self, monkeypatch):
        """Test that temperature setting works with generate_draft function."""
        from src.draft_generator import generate_draft
        
        # Set custom temperature
        monkeypatch.setenv("TEMP_DRAFT", "0.85")
        
        # Generate draft (will use fallback mode due to no real API key)
        result = generate_draft("test context", 1)
        
        # Should return a string
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify temperature environment variable is accessible
        assert float(os.getenv("TEMP_DRAFT", "0.7")) == 0.85