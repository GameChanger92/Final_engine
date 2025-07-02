"""
Integration tests for Beat Planner pipeline functionality
"""

from unittest.mock import patch

from src.beat_planner import plan_beats


class TestPipelineBeatIntegration:
    """Integration tests for beat planning in the pipeline."""

    @patch("src.beat_planner.call_llm")
    @patch("src.beat_planner.run_with_retry")
    def test_run_pipeline_beat_structure(self, mock_retry, mock_llm):
        """Test run_pipeline(7) execution includes Beat dict structure."""
        # Mock successful LLM responses
        mock_retry.side_effect = lambda func: func()
        mock_llm.return_value = """
        beat_1: "파이프라인 테스트 비트 1"
        beat_2: "파이프라인 테스트 비트 2"
        beat_3: "파이프라인 테스트 비트 3"
        beat_tp: "파이프라인 테스트 전환점"
        """

        # Run the beat planning for episode 7
        result = plan_beats(7, [])

        # Verify the structure matches Scene Maker v2 specifications
        assert isinstance(result, dict)
        assert "ep_7" in result

        episode_data = result["ep_7"]
        assert isinstance(episode_data, dict)

        # Check all sequences have the correct seq_x/beat_y structure
        for seq_num in range(1, 7):
            seq_key = f"seq_{seq_num}"
            assert seq_key in episode_data

            seq_beats = episode_data[seq_key]
            assert isinstance(seq_beats, dict)

            # Verify beat structure compatible with Scene Maker v2
            required_beat_keys = ["beat_1", "beat_2", "beat_3", "beat_tp"]
            for beat_key in required_beat_keys:
                assert beat_key in seq_beats
                assert isinstance(seq_beats[beat_key], str)
                assert len(seq_beats[beat_key]) > 0

    @patch("src.beat_planner.call_llm")
    def test_pipeline_beat_compatibility_scene_maker_v2(self, mock_llm):
        """Test that beat output structure is compatible with Scene Maker v2."""
        # Mock LLM output
        mock_llm.return_value = """
        beat_1: "씬 메이커 호환성 테스트 비트 1"
        beat_2: "씬 메이커 호환성 테스트 비트 2"
        beat_3: "씬 메이커 호환성 테스트 비트 3"
        beat_tp: "씬 메이커 호환성 테스트 전환점"
        """

        with patch("src.beat_planner.run_with_retry") as mock_retry:
            mock_retry.side_effect = lambda func: func()

            result = plan_beats(3, ["previous beat context"])

            # Test that the structure can be consumed by Scene Maker v2
            episode_data = result["ep_3"]

            # Simulate Scene Maker v2 usage pattern
            for seq_key, seq_beats in episode_data.items():
                assert seq_key.startswith("seq_")

                for beat_key, beat_desc in seq_beats.items():
                    assert beat_key in ["beat_1", "beat_2", "beat_3", "beat_tp"]

                    # Scene Maker v2 should be able to use these descriptions
                    assert isinstance(beat_desc, str)
                    assert len(beat_desc.strip()) > 0

                    # Check Korean content (as per spec)
                    assert any(ord(char) >= 0xAC00 and ord(char) <= 0xD7AF for char in beat_desc)

    def test_pipeline_beat_act_sequence_distribution(self):
        """Test that pipeline correctly distributes beats across 3-Act structure."""
        with patch("src.beat_planner.call_llm") as mock_llm:
            mock_llm.return_value = """
            beat_1: "액트 구조 테스트 비트 1"
            beat_2: "액트 구조 테스트 비트 2"
            beat_3: "액트 구조 테스트 비트 3"
            beat_tp: "액트 구조 테스트 전환점"
            """

            with patch("src.beat_planner.run_with_retry") as mock_retry:
                mock_retry.side_effect = lambda func: func()

                result = plan_beats(5, [])
                episode_data = result["ep_5"]

                # Verify 6 sequences total (3-Act structure)
                assert len(episode_data) == 6

                # Act 1 (Setup): Sequences 1-2
                assert "seq_1" in episode_data
                assert "seq_2" in episode_data

                # Act 2 (Confrontation): Sequences 3-4
                assert "seq_3" in episode_data
                assert "seq_4" in episode_data

                # Act 3 (Resolution): Sequences 5-6
                assert "seq_5" in episode_data
                assert "seq_6" in episode_data

                # Each sequence should have exactly 4 beats
                for seq_key in episode_data:
                    assert len(episode_data[seq_key]) == 4

    @patch("src.beat_planner.logger")
    def test_pipeline_logging_output(self, mock_logger):
        """Test that pipeline produces expected logging output."""
        with patch("src.beat_planner.call_llm") as mock_llm:
            mock_llm.return_value = """
            beat_1: "로깅 테스트 비트 1"
            beat_2: "로깅 테스트 비트 2"
            beat_3: "로깅 테스트 비트 3"
            beat_tp: "로깅 테스트 전환점"
            """

            with patch("src.beat_planner.run_with_retry") as mock_retry:
                mock_retry.side_effect = lambda func: func()

                plan_beats(1, [])

                # Check that expected log messages were called
                info_calls = [call for call in mock_logger.info.call_args_list]

                # Should log beat generation for each sequence
                act_seq_logs = [
                    call
                    for call in info_calls
                    if any(
                        "Beat Planner…" in str(arg) and "Beats generated" in str(arg)
                        for arg in call[0]
                    )
                ]

                # Should have 6 log entries (one per sequence)
                assert len(act_seq_logs) == 6

    def test_pipeline_fallback_behavior(self):
        """Test pipeline behavior when LLM fails and fallback is used."""
        with patch("src.beat_planner.call_llm") as mock_llm:
            # Simulate LLM failure
            from src.exceptions import RetryException

            mock_llm.side_effect = RetryException("LLM failed", guard_name="llm_call")

            result = plan_beats(10, [])

            # Should still return valid structure using fallbacks
            assert "ep_10" in result
            episode_data = result["ep_10"]

            # All sequences should be present with fallback content
            assert len(episode_data) == 6

            for seq_num in range(1, 7):
                seq_key = f"seq_{seq_num}"
                assert seq_key in episode_data

                seq_beats = episode_data[seq_key]
                assert len(seq_beats) == 4

                # Fallback content should indicate the act and sequence
                for beat_key in ["beat_1", "beat_2", "beat_3", "beat_tp"]:
                    beat_content = seq_beats[beat_key]
                    assert f"Seq{seq_num}" in beat_content

                    # Should indicate correct act
                    if seq_num in [1, 2]:
                        assert "Act 1" in beat_content
                    elif seq_num in [3, 4]:
                        assert "Act 2" in beat_content
                    else:  # seq_num in [5, 6]
                        assert "Act 3" in beat_content
