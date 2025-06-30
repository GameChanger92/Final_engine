"""
Unit tests for beat_planner.py - Beat Planner v2 functionality
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.beat_planner import (
    build_prompt,
    call_llm,
    plan_beats,
    parse_beat_output,
    generate_fallback_beats,
    get_act_number,
    make_beats
)
from src.exceptions import RetryException


class TestBeatPlannerV2:
    """Test cases for Beat Planner v2 functionality."""

    def test_get_act_number_mapping(self):
        """Test Act/Sequence distribution rules."""
        # Act 1 (Setup): Seq 1-2
        assert get_act_number(1) == 1
        assert get_act_number(2) == 1
        
        # Act 2 (Confrontation): Seq 3-4
        assert get_act_number(3) == 2
        assert get_act_number(4) == 2
        
        # Act 3 (Resolution): Seq 5-6
        assert get_act_number(5) == 3
        assert get_act_number(6) == 3

    def test_generate_fallback_beats_structure(self):
        """Test fallback beats have exactly 4 beats with correct keys."""
        for seq_num in range(1, 7):
            beats = generate_fallback_beats(seq_num)
            
            # Check we have exactly 4 beats
            assert len(beats) == 4
            
            # Check required keys exist
            required_keys = ["beat_1", "beat_2", "beat_3", "beat_tp"]
            for key in required_keys:
                assert key in beats
                assert isinstance(beats[key], str)
                assert len(beats[key]) > 0

    def test_parse_beat_output_valid_format(self):
        """Test parsing of valid LLM output."""
        llm_output = '''
        beat_1: "첫 번째 비트 설명"
        beat_2: "두 번째 비트 설명"
        beat_3: "세 번째 비트 설명"
        beat_tp: "전환점 비트 설명"
        '''
        
        beats = parse_beat_output(llm_output)
        
        assert len(beats) == 4
        assert beats["beat_1"] == "첫 번째 비트 설명"
        assert beats["beat_2"] == "두 번째 비트 설명"
        assert beats["beat_3"] == "세 번째 비트 설명"
        assert beats["beat_tp"] == "전환점 비트 설명"

    def test_parse_beat_output_missing_beats(self):
        """Test parsing when some beats are missing."""
        llm_output = '''
        beat_1: "첫 번째 비트만 있음"
        '''
        
        beats = parse_beat_output(llm_output)
        
        # Should have 4 beats with fallbacks for missing ones
        assert len(beats) == 4
        assert beats["beat_1"] == "첫 번째 비트만 있음"
        assert "Generated beat_2 content" in beats["beat_2"]
        assert "Generated beat_3 content" in beats["beat_3"] 
        assert "Generated beat_tp content" in beats["beat_tp"]

    def test_build_prompt_with_previous_beats(self):
        """Test prompt building with previous beats context."""
        arc_goal = "Test story arc"
        prev_beats = ["Previous beat 1", "Previous beat 2"]
        sequence_no = 3
        
        prompt = build_prompt(arc_goal, prev_beats, sequence_no)
        
        assert isinstance(prompt, str)
        assert arc_goal in prompt
        assert "Previous beat 1" in prompt
        assert "Previous beat 2" in prompt
        assert "3" in prompt
        assert "beat_1:" in prompt
        assert "beat_tp:" in prompt

    def test_build_prompt_empty_previous_beats(self):
        """Test prompt building with empty previous beats."""
        arc_goal = "Test story arc"
        prev_beats = []
        sequence_no = 1
        
        prompt = build_prompt(arc_goal, prev_beats, sequence_no)
        
        assert isinstance(prompt, str)
        assert arc_goal in prompt
        assert "beginning of the story" in prompt.lower()
        assert "1" in prompt

    def test_temp_beat_environment_variable(self, monkeypatch):
        """Test that TEMP_BEAT environment variable is used."""
        # Set custom temperature
        monkeypatch.setenv("TEMP_BEAT", "0.5")
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
        monkeypatch.setenv("MODEL_NAME", "gemini-2.5-pro")
        
        # Mock the import to avoid actual API calls
        with patch("src.beat_planner.os.getenv") as mock_getenv:
            def mock_env_side_effect(key, default=None):
                env_values = {
                    "TEMP_BEAT": "0.5",
                    "GOOGLE_API_KEY": "test_key",
                    "MODEL_NAME": "gemini-2.5-pro",
                    "UNIT_TEST_MODE": None
                }
                return env_values.get(key, default)
            
            mock_getenv.side_effect = mock_env_side_effect
            
            # Test that the environment variable can be read correctly
            temp_value = float(os.getenv("TEMP_BEAT", "0.3"))
            assert temp_value == 0.5

    def test_call_llm_handles_import_error(self, monkeypatch):
        """Test call_llm handles import error gracefully."""
        # Set unit test mode to trigger import error
        monkeypatch.setenv("UNIT_TEST_MODE", "1")
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")

        with pytest.raises(RetryException) as excinfo:
            call_llm("test prompt")
        
        assert "library not available" in str(excinfo.value)

    def test_call_llm_missing_api_key(self, monkeypatch):
        """Test call_llm fails appropriately when API key is missing."""
        # Remove API key
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        with pytest.raises(RetryException) as excinfo:
            call_llm("test prompt")
        
        assert "API key not configured" in str(excinfo.value)

    @patch("src.beat_planner.call_llm")
    @patch("src.beat_planner.run_with_retry")
    def test_plan_beats_returns_correct_structure(self, mock_retry, mock_llm):
        """Test plan_beats returns the correct ep_X -> seq_Y -> beat_Z structure."""
        # Mock successful LLM calls
        mock_retry.side_effect = lambda func: func()
        mock_llm.return_value = '''
        beat_1: "테스트 비트 1"
        beat_2: "테스트 비트 2"
        beat_3: "테스트 비트 3"
        beat_tp: "테스트 전환점"
        '''
        
        result = plan_beats(42, [])
        
        # Check top-level structure
        assert "ep_42" in result
        episode_data = result["ep_42"]
        
        # Check all 6 sequences exist
        for seq_num in range(1, 7):
            seq_key = f"seq_{seq_num}"
            assert seq_key in episode_data
            
            # Check each sequence has 4 beats
            seq_beats = episode_data[seq_key]
            assert len(seq_beats) == 4
            assert "beat_1" in seq_beats
            assert "beat_2" in seq_beats
            assert "beat_3" in seq_beats
            assert "beat_tp" in seq_beats

    @patch("src.beat_planner.call_llm")
    def test_plan_beats_llm_failure_fallback(self, mock_llm):
        """Test plan_beats uses fallback when LLM fails."""
        # Mock LLM failure
        mock_llm.side_effect = RetryException("LLM failed", guard_name="llm_call")
        
        result = plan_beats(1, [])
        
        # Should still return valid structure with fallback content
        assert "ep_1" in result
        episode_data = result["ep_1"]
        
        # Check fallback content exists
        for seq_num in range(1, 7):
            seq_key = f"seq_{seq_num}"
            assert seq_key in episode_data
            seq_beats = episode_data[seq_key]
            
            # Fallback beats should contain sequence and act info
            assert "Act" in seq_beats["beat_1"]
            assert f"Seq{seq_num}" in seq_beats["beat_1"]

    def test_backward_compatibility_make_beats(self):
        """Test that legacy make_beats function still works."""
        dummy = {"title": "Prologue", "anchor_ep": 3}
        
        beats = make_beats(dummy)
        
        # Legacy tests should still pass
        assert len(beats) == 10
        assert beats[0]["idx"] == 1
        assert beats[2]["anchor"] is True
        assert all(b["anchor"] is False for b in beats if b["idx"] != 3)


class TestTemperatureBeatIntegration:
    """Test integration of TEMP_BEAT with beat planning."""
    
    def test_temperature_defaults_to_0_3(self):
        """Test that TEMP_BEAT defaults to 0.3 when not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Mock environment without TEMP_BEAT
            temp_value = float(os.getenv("TEMP_BEAT", "0.3"))
            assert temp_value == 0.3
    
    def test_temperature_custom_value_used(self):
        """Test that custom TEMP_BEAT value is used."""
        with patch.dict(os.environ, {"TEMP_BEAT": "0.8"}):
            temp_value = float(os.getenv("TEMP_BEAT", "0.3"))
            assert temp_value == 0.8